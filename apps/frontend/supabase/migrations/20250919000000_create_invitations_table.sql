CREATE TABLE IF NOT EXISTS "public"."invitations" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "email" text NOT NULL,
  "org_name" text NOT NULL,
  "org_id" uuid NOT NULL,
  "invited_by" uuid NOT NULL,
  "status" text NOT NULL DEFAULT 'pending',
  "expires_at" timestamp with time zone NOT NULL DEFAULT (now() + interval '7 days'),
  "accepted_at" timestamp with time zone,
  "accepted_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "deleted_at" timestamp with time zone,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("invited_by") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE,
  FOREIGN KEY ("accepted_by") REFERENCES "public"."user_profiles"("id") ON DELETE SET NULL,
  CONSTRAINT "valid_status" CHECK (status IN ('pending', 'accepted', 'expired', 'revoked')),
  CONSTRAINT "email_format" CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX "idx_invitations_org_id" ON "public"."invitations" ("org_id");
CREATE INDEX "idx_invitations_email" ON "public"."invitations" ("email");
CREATE INDEX "idx_invitations_status" ON "public"."invitations" ("status");
CREATE INDEX "idx_invitations_expires_at" ON "public"."invitations" ("expires_at");

CREATE UNIQUE INDEX "idx_unique_pending_invitations"
ON "public"."invitations" (LOWER(email), org_id)
WHERE status = 'pending' AND deleted_at IS NULL;

ALTER TABLE "public"."invitations" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view org invitations" ON "public"."invitations"
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM "public"."users_by_organization" ubo
    WHERE ubo.org_id = invitations.org_id
    AND ubo.user_id = auth.uid()
    AND ubo.deleted_at IS NULL
  )
);

CREATE POLICY "Users can view invitations sent to them" ON "public"."invitations"
FOR SELECT USING (
  LOWER(email) = LOWER((SELECT email FROM "public"."user_profiles" WHERE id = auth.uid()))
);

CREATE POLICY "Users can create org invitations" ON "public"."invitations"
FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM "public"."user_profiles" up
    WHERE up.id = invited_by AND up.id = auth.uid()
  ) AND
  EXISTS (
    SELECT 1 FROM "public"."users_by_organization" ubo
    WHERE ubo.org_id = invitations.org_id
    AND ubo.user_id = auth.uid()
    AND ubo.deleted_at IS NULL
  )
);

CREATE POLICY "Users can update own invitations" ON "public"."invitations"
FOR UPDATE USING (
  EXISTS (
    SELECT 1 FROM "public"."user_profiles" up
    WHERE up.id = invited_by AND up.id = auth.uid()
  )
);

CREATE OR REPLACE FUNCTION "public"."validate_invitation_status_transition"()
RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.status != 'pending' THEN
      RAISE EXCEPTION 'New invitations must have status "pending"';
    END IF;
    RETURN NEW;
  END IF;

  IF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
    CASE OLD.status
      WHEN 'pending' THEN
        IF NEW.status NOT IN ('accepted', 'expired', 'revoked') THEN
          RAISE EXCEPTION 'Invalid status transition from "%" to "%"', OLD.status, NEW.status;
        END IF;
      WHEN 'accepted' THEN
        RAISE EXCEPTION 'Cannot change status from "accepted" to "%"', NEW.status;
      WHEN 'expired' THEN
        RAISE EXCEPTION 'Cannot change status from "expired" to "%"', NEW.status;
      WHEN 'revoked' THEN
        RAISE EXCEPTION 'Cannot change status from "revoked" to "%"', NEW.status;
      ELSE
        RAISE EXCEPTION 'Unknown status "%"', OLD.status;
    END CASE;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER "invitation_status_validation_trigger"
  BEFORE INSERT OR UPDATE ON "public"."invitations"
  FOR EACH ROW EXECUTE FUNCTION "public"."validate_invitation_status_transition"();

CREATE OR REPLACE FUNCTION "public"."expire_old_invitations"()
RETURNS void AS $$
BEGIN
  UPDATE public.invitations
  SET status = 'expired', updated_at = now()
  WHERE status = 'pending'
  AND expires_at < now();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION "public"."cleanup_orphaned_invitations"()
RETURNS void AS $$
BEGIN
  UPDATE public.invitations
  SET status = 'revoked',
      updated_at = now(),
      deleted_at = now()
  WHERE status = 'pending'
  AND (
    NOT EXISTS (
      SELECT 1 FROM public.users_by_organization ubo
      WHERE ubo.user_id = invitations.invited_by
      AND ubo.org_id = invitations.org_id
      AND ubo.deleted_at IS NULL
    )
    OR
    NOT EXISTS (
      SELECT 1 FROM public.user_profiles up
      WHERE up.id = invitations.invited_by
    )
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION "public"."accept_invitation"(p_invitation_id uuid, p_user_id uuid)
RETURNS boolean AS $$
DECLARE
  invitation_record record;
  user_email text;
BEGIN
  PERFORM expire_old_invitations();
  PERFORM cleanup_orphaned_invitations();

  SELECT email INTO user_email
  FROM "public"."user_profiles"
  WHERE id = p_user_id;

  IF user_email IS NULL THEN
    RAISE EXCEPTION 'User profile not found for user ID: %', p_user_id;
  END IF;

  SELECT * INTO invitation_record
  FROM public.invitations
  WHERE id = p_invitation_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Invalid invitation ID';
  END IF;

  IF invitation_record.status != 'pending' THEN
    RAISE EXCEPTION 'Invitation has already been % or is no longer valid', invitation_record.status;
  END IF;

  IF invitation_record.expires_at <= now() THEN
    RAISE EXCEPTION 'Invitation has expired';
  END IF;

  IF LOWER(invitation_record.email) != LOWER(user_email) THEN
    RAISE EXCEPTION 'Invitation email does not match user email';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.users_by_organization
    WHERE user_id = p_user_id
    AND org_id = invitation_record.org_id
    AND deleted_at IS NULL
  ) THEN
    UPDATE public.invitations
    SET status = 'accepted',
        accepted_at = now(),
        accepted_by = p_user_id,
        updated_at = now()
    WHERE id = invitation_record.id;

    RETURN true;
  END IF;

  INSERT INTO public.users_by_organization (user_id, org_id, user_role)
  VALUES (p_user_id, invitation_record.org_id, 'member');

  UPDATE public.invitations
  SET status = 'accepted',
      accepted_at = now(),
      accepted_by = p_user_id,
      updated_at = now()
  WHERE id = invitation_record.id;

  RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT ALL ON TABLE "public"."invitations" TO "anon";
GRANT ALL ON TABLE "public"."invitations" TO "authenticated";
GRANT ALL ON TABLE "public"."invitations" TO "service_role";

GRANT ALL ON FUNCTION "public"."expire_old_invitations"() TO "anon";
GRANT ALL ON FUNCTION "public"."expire_old_invitations"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."expire_old_invitations"() TO "service_role";

GRANT ALL ON FUNCTION "public"."cleanup_orphaned_invitations"() TO "anon";
GRANT ALL ON FUNCTION "public"."cleanup_orphaned_invitations"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."cleanup_orphaned_invitations"() TO "service_role";

GRANT ALL ON FUNCTION "public"."validate_invitation_status_transition"() TO "anon";
GRANT ALL ON FUNCTION "public"."validate_invitation_status_transition"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."validate_invitation_status_transition"() TO "service_role";

GRANT ALL ON FUNCTION "public"."accept_invitation"(uuid, uuid) TO "anon";
GRANT ALL ON FUNCTION "public"."accept_invitation"(uuid, uuid) TO "authenticated";
GRANT ALL ON FUNCTION "public"."accept_invitation"(uuid, uuid) TO "service_role";
