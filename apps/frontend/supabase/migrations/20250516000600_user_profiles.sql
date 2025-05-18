drop policy "Public profiles are viewable by everyone." on "public"."profiles";

drop policy "Users can insert their own profile." on "public"."profiles";

drop policy "Users can update own profile." on "public"."profiles";

drop policy "Organizations are viewable by public." on "public"."users_by_organization";

revoke delete on table "public"."profiles" from "anon";

revoke insert on table "public"."profiles" from "anon";

revoke references on table "public"."profiles" from "anon";

revoke select on table "public"."profiles" from "anon";

revoke trigger on table "public"."profiles" from "anon";

revoke truncate on table "public"."profiles" from "anon";

revoke update on table "public"."profiles" from "anon";

revoke delete on table "public"."profiles" from "authenticated";

revoke insert on table "public"."profiles" from "authenticated";

revoke references on table "public"."profiles" from "authenticated";

revoke select on table "public"."profiles" from "authenticated";

revoke trigger on table "public"."profiles" from "authenticated";

revoke truncate on table "public"."profiles" from "authenticated";

revoke update on table "public"."profiles" from "authenticated";

revoke delete on table "public"."profiles" from "service_role";

revoke insert on table "public"."profiles" from "service_role";

revoke references on table "public"."profiles" from "service_role";

revoke select on table "public"."profiles" from "service_role";

revoke trigger on table "public"."profiles" from "service_role";

revoke truncate on table "public"."profiles" from "service_role";

revoke update on table "public"."profiles" from "service_role";

alter table "public"."profiles" drop constraint "profiles_id_fkey";

alter table "public"."profiles" drop constraint "profiles_username_key";

alter table "public"."profiles" drop constraint "username_length";

alter table "public"."profiles" drop constraint "profiles_pkey";

drop table "public"."profiles";

create table "public"."user_profiles" (
    "id" uuid not null,
    "updated_at" timestamp with time zone,
    "username" text,
    "full_name" text,
    "avatar_url" text,
    "website" text,
    "email" text
);


alter table "public"."user_profiles" enable row level security;

CREATE UNIQUE INDEX user_profiles_email_key ON public.user_profiles USING btree (email);

CREATE UNIQUE INDEX profiles_pkey ON public.user_profiles USING btree (id);

CREATE UNIQUE INDEX profiles_username_key ON public.user_profiles USING btree (username);

alter table "public"."user_profiles" add constraint "profiles_pkey" PRIMARY KEY using index "profiles_pkey";

alter table "public"."admin_users" add constraint "admin_users_user_id_fkey" FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."admin_users" validate constraint "admin_users_user_id_fkey";

alter table "public"."api_keys" add constraint "api_keys_user_id_fkey1" FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON UPDATE CASCADE not valid;

alter table "public"."api_keys" validate constraint "api_keys_user_id_fkey1";

alter table "public"."organizations" add constraint "organizations_created_by_fkey1" FOREIGN KEY (created_by) REFERENCES user_profiles(id) ON UPDATE CASCADE not valid;

alter table "public"."organizations" validate constraint "organizations_created_by_fkey1";

alter table "public"."user_profiles" add constraint "profiles_id_fkey" FOREIGN KEY (id) REFERENCES auth.users(id) not valid;

alter table "public"."user_profiles" validate constraint "profiles_id_fkey";

alter table "public"."user_profiles" add constraint "profiles_username_key" UNIQUE using index "profiles_username_key";

alter table "public"."user_profiles" add constraint "user_profiles_email_key" UNIQUE using index "user_profiles_email_key";

alter table "public"."user_profiles" add constraint "username_length" CHECK ((char_length(username) >= 3)) not valid;

alter table "public"."user_profiles" validate constraint "username_length";

alter table "public"."users_by_organization" add constraint "users_by_organization_user_id_fkey1" FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."users_by_organization" validate constraint "users_by_organization_user_id_fkey1";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.prevent_update_api_keys()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$BEGIN
  IF NEW.api_key <> OLD.api_key THEN
    RAISE EXCEPTION 'changing "api_key" values are not allowed';
  END IF;

  RETURN NEW;
END;$function$
;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$begin
  insert into public.profiles (id, full_name, avatar_url, email)
  values (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url', new.raw_user_meta_data->>'email');
  return new;
end;$function$
;

grant delete on table "public"."user_profiles" to "anon";

grant insert on table "public"."user_profiles" to "anon";

grant references on table "public"."user_profiles" to "anon";

grant select on table "public"."user_profiles" to "anon";

grant trigger on table "public"."user_profiles" to "anon";

grant truncate on table "public"."user_profiles" to "anon";

grant update on table "public"."user_profiles" to "anon";

grant delete on table "public"."user_profiles" to "authenticated";

grant insert on table "public"."user_profiles" to "authenticated";

grant references on table "public"."user_profiles" to "authenticated";

grant select on table "public"."user_profiles" to "authenticated";

grant trigger on table "public"."user_profiles" to "authenticated";

grant truncate on table "public"."user_profiles" to "authenticated";

grant update on table "public"."user_profiles" to "authenticated";

grant delete on table "public"."user_profiles" to "service_role";

grant insert on table "public"."user_profiles" to "service_role";

grant references on table "public"."user_profiles" to "service_role";

grant select on table "public"."user_profiles" to "service_role";

grant trigger on table "public"."user_profiles" to "service_role";

grant truncate on table "public"."user_profiles" to "service_role";

grant update on table "public"."user_profiles" to "service_role";

create policy "Public profiles are viewable by everyone."
on "public"."user_profiles"
as permissive
for select
to public
using (true);


create policy "Users can insert their own profile."
on "public"."user_profiles"
as permissive
for insert
to public
with check ((auth.uid() = id));


create policy "Users can update own profile."
on "public"."user_profiles"
as permissive
for update
to public
using ((auth.uid() = id));


create policy "Organizations are viewable by public"
on "public"."users_by_organization"
as permissive
for select
to public
using (true);


CREATE TRIGGER prevent_update_api_keys BEFORE UPDATE ON public.api_keys FOR EACH ROW EXECUTE FUNCTION prevent_update_api_keys();


