CREATE UNIQUE INDEX api_keys_api_key_key ON public.api_keys USING btree (api_key);

alter table "public"."api_keys" add constraint "api_keys_api_key_key" UNIQUE using index "api_keys_api_key_key";


