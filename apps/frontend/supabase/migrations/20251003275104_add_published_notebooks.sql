create table "public"."published_notebooks" (
    "id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "deleted_at" timestamp with time zone,
    "data" text not null,
    "published_by" uuid not null,
    "notebook_id" uuid not null
);


alter table "public"."published_notebooks" enable row level security;

CREATE UNIQUE INDEX published_notebooks_pkey ON public.published_notebooks USING btree (id);

alter table "public"."published_notebooks" add constraint "published_notebooks_pkey" PRIMARY KEY using index "published_notebooks_pkey";

CREATE UNIQUE INDEX published_notebooks_notebook_id ON public.published_notebooks USING btree (notebook_id);

alter table "public"."published_notebooks" add constraint "published_notebooks_notebook_id_fkey" FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON UPDATE CASCADE ON DELETE CASCADE not valid;

alter table "public"."published_notebooks" validate constraint "published_notebooks_notebook_id_fkey";

alter table "public"."published_notebooks" add constraint "published_notebooks_published_by_fkey" FOREIGN KEY (published_by) REFERENCES auth.users(id) not valid;

alter table "public"."published_notebooks" validate constraint "published_notebooks_published_by_fkey";

create policy "Published notebooks are viewable by everyone"
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
with check (( SELECT auth.uid() AS uid) = published_by AND (( SELECT check_org_membership(auth.uid(), ( SELECT notebooks.org_id
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
with check (( SELECT auth.uid() AS uid) = published_by);

CREATE OR REPLACE FUNCTION public.get_published_notebook_by_names(p_notebook_name text, p_org_name text)
 RETURNS SETOF published_notebooks
 LANGUAGE sql
 SECURITY DEFINER
AS $$
  select pn.*
  from published_notebooks pn
  join notebooks n on pn.notebook_id = n.id
  join organizations o on n.org_id = o.id
  where n.notebook_name = get_published_notebook_by_names.p_notebook_name
  and o.org_name = get_published_notebook_by_names.p_org_name
  and pn.deleted_at is null;
$$;