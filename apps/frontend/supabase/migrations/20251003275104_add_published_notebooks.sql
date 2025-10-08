create table "public"."published_notebooks" (
    "id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "deleted_at" timestamp with time zone,
    "data" text not null,
    "updated_by" uuid,
    "notebook_id" uuid not null
);


alter table "public"."published_notebooks" enable row level security;

CREATE UNIQUE INDEX published_notebooks_pkey ON public.published_notebooks USING btree (id);

alter table "public"."published_notebooks" add constraint "published_notebooks_pkey" PRIMARY KEY using index "published_notebooks_pkey";

CREATE UNIQUE INDEX published_notebooks_notebook_id ON public.published_notebooks USING btree (notebook_id);

alter table "public"."published_notebooks" add constraint "published_notebooks_notebook_id_fkey" FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON UPDATE CASCADE ON DELETE SET NULL not valid;

alter table "public"."published_notebooks" validate constraint "published_notebooks_notebook_id_fkey";

alter table "public"."published_notebooks" add constraint "published_notebooks_updated_by_fkey" FOREIGN KEY (updated_by) REFERENCES auth.users(id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."published_notebooks" validate constraint "published_notebooks_updated_by_fkey";

create policy "Users can view published notebooks"
on "public"."published_notebooks"
as permissive
for select
to "authenticated"
using ((( SELECT check_org_membership(auth.uid(), ( SELECT notebooks.org_id
           FROM notebooks
          WHERE (notebooks.id = published_notebooks.notebook_id)))) = true));

create policy "Users can publish notebook"
on "public"."published_notebooks"
as permissive
for insert
to "authenticated"
with check (( SELECT auth.uid() AS uid) = updated_by AND (( SELECT check_org_membership(auth.uid(), ( SELECT notebooks.org_id
           FROM notebooks
          WHERE (notebooks.id = published_notebooks.notebook_id)))) = true));


create policy "Users can update publish notebook"
on "public"."published_notebooks"
as permissive
for update
to "authenticated"
using (((( SELECT check_org_membership(auth.uid(), ( SELECT notebooks.org_id
           FROM notebooks
          WHERE (notebooks.id = published_notebooks.notebook_id)))) = true)))
with check (( SELECT auth.uid() AS uid) = updated_by);
