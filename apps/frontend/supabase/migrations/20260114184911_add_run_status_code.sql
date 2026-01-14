-- Status code for runs should reflect an "http" status code style:
-- * 200s for success
-- * 300s are not used as redirects don't make sense in this context
-- * 400s for client errors
-- * 500s for server errors
-- This allows for us to use these status codes to respond in REST APIs 
-- and also gives us a familiar way to categorize different types of run results.
ALTER TABLE "public"."run" ADD COLUMN "status_code" integer array;