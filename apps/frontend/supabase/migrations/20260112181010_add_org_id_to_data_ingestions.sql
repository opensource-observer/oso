ALTER TABLE data_ingestions ADD COLUMN org_id uuid;

UPDATE data_ingestions
SET org_id = datasets.org_id
FROM datasets
WHERE data_ingestions.dataset_id = datasets.id;

ALTER TABLE data_ingestions ALTER COLUMN org_id SET NOT NULL;

ALTER TABLE data_ingestions
ADD CONSTRAINT fk_data_ingestions_org_id
FOREIGN KEY (org_id) REFERENCES organizations(id);

ALTER TABLE data_ingestions ADD COLUMN name text;

UPDATE data_ingestions
SET name = datasets.name
FROM datasets
WHERE data_ingestions.dataset_id = datasets.id;

ALTER TABLE data_ingestions ALTER COLUMN name SET NOT NULL;
