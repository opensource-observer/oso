create table "public"."published_notebooks" (
    "id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "deleted_at" timestamp with time zone,
    "data" text not null,
    "published_by" uuid not null,
    "notebook_id" uuid not null,
    "name" text not null,
    CONSTRAINT "published_notebook_name_format" CHECK (("name" ~ '^[a-z][a-z0-9_-]*$'::"text"))
);


alter table "public"."published_notebooks" enable row level security;

CREATE UNIQUE INDEX published_notebooks_pkey ON public.published_notebooks USING btree (id);

alter table "public"."published_notebooks" add constraint "published_notebooks_pkey" PRIMARY KEY using index "published_notebooks_pkey";

CREATE UNIQUE INDEX published_notebooks_notebook_id ON public.published_notebooks USING btree (notebook_id);

alter table "public"."published_notebooks" add constraint "published_notebooks_notebook_id_fkey" FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."published_notebooks" validate constraint "published_notebooks_notebook_id_fkey";

alter table "public"."published_notebooks" add constraint "published_notebooks_published_by_fkey" FOREIGN KEY (published_by) REFERENCES auth.users(id) not valid;

alter table "public"."published_notebooks" validate constraint "published_notebooks_published_by_fkey";

CREATE UNIQUE INDEX published_notebooks_name ON public.published_notebooks USING btree (name);


create policy "Published notebooks are viewable by everyone"
on "public"."published_notebooks"
as permissive
for select
to public
using (true);


create policy "Users can publish notebook"
on "public"."published_notebooks"
as permissive
for insert
to public
with check (((( SELECT auth.uid() AS uid) = published_by) AND (( SELECT check_org_membership(published_notebooks.published_by, ( SELECT notebooks.org_id
           FROM notebooks
          WHERE (notebooks.id = published_notebooks.notebook_id))) AS check_org_membership) = true)));
