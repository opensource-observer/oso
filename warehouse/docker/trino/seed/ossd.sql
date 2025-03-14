CREATE SCHEMA IF NOT EXISTS bigquery.ossd;

CREATE TABLE IF NOT EXISTS bigquery.ossd.collections (
   version bigint,
   name varchar,
   display_name varchar,
   projects array(varchar) NOT NULL,
   description varchar,
   sha varbinary,
   committed_time timestamp(6) with time zone
);

INSERT INTO
   bigquery.ossd.collections (
      version,
      name,
      display_name,
      projects,
      description,
      sha,
      committed_time
   )
VALUES
   (
      1,
      'collection1',
      'Collection 1',
      ARRAY ['project1', 'project2'],
      'Description 1',
      NULL,
      current_timestamp
   ),
   (
      2,
      'collection2',
      'Collection 2',
      ARRAY ['project3', 'project4'],
      'Description 2',
      NULL,
      current_timestamp
   );

CREATE TABLE IF NOT EXISTS bigquery.ossd.projects (
   version bigint,
   name varchar,
   display_name varchar,
   github array(ROW(url varchar)) NOT NULL,
   description varchar,
   websites array(ROW(url varchar)) NOT NULL,
   social ROW(
      discord array(ROW(url varchar)),
      farcaster array(ROW(url varchar)),
      telegram array(ROW(url varchar)),
      twitter array(ROW(url varchar))
   ),
   blockchain array(
      ROW(
         address varchar,
         name varchar,
         networks array(varchar),
         tags array(varchar)
      )
   ) NOT NULL,
   npm array(ROW(url varchar)) NOT NULL,
   "go" array(ROW(url varchar)) NOT NULL,
   open_collective array(ROW(url varchar)) NOT NULL,
   sha varbinary,
   committed_time timestamp(6) with time zone
);

INSERT INTO
   bigquery.ossd.projects (
      version,
      name,
      display_name,
      github,
      description,
      websites,
      social,
      blockchain,
      npm,
      "go",
      open_collective,
      sha,
      committed_time
   )
VALUES
   (
      1,
      'project1',
      'Project 1',
      ARRAY [ROW('https://github.com/project1')],
      'Description 1',
      ARRAY [ROW('https://project1.com')],
      ROW(
         ARRAY [ROW('https://discord.com/project1')],
         ARRAY [ROW('https://farcaster.com/project1')],
         ARRAY [ROW('https://telegram.com/project1')],
         ARRAY [ROW('https://twitter.com/project1')]
      ),
      ARRAY [ROW('address1', 'Blockchain 1', ARRAY['network1'],
      ARRAY ['tag1']
   ) ],
   ARRAY [ROW('https://npmjs.com/project1')],
   ARRAY [ROW('https://go.com/project1')],
   ARRAY [ROW('https://opencollective.com/project1')],
   NULL,
   current_timestamp
),
(
   2,
   'project2',
   'Project 2',
   ARRAY [ROW('https://github.com/project2')],
   'Description 2',
   ARRAY [ROW('https://project2.com')],
   ROW(
      ARRAY [ROW('https://discord.com/project2')],
      ARRAY [ROW('https://farcaster.com/project2')],
      ARRAY [ROW('https://telegram.com/project2')],
      ARRAY [ROW('https://twitter.com/project2')]
   ),
   ARRAY [ROW('address2', 'Blockchain 2', ARRAY['network2'],
   ARRAY ['tag2']
) ],
ARRAY [ROW('https://npmjs.com/project2')],
ARRAY [ROW('https://go.com/project2')],
ARRAY [ROW('https://opencollective.com/project2')],
NULL,
current_timestamp
);

CREATE TABLE IF NOT EXISTS bigquery.ossd.repositories (
   ingestion_time timestamp(6) with time zone,
   id bigint,
   node_id varchar,
   name_with_owner varchar,
   url varchar,
   name varchar,
   is_fork boolean,
   branch varchar,
   fork_count bigint,
   star_count bigint,
   watcher_count bigint,
   license_spdx_id varchar,
   license_name varchar,
   language varchar,
   _dlt_load_id varchar NOT NULL,
   _dlt_id varchar NOT NULL,
   owner varchar,
   created_at timestamp(6) with time zone,
   updated_at timestamp(6) with time zone
);

INSERT INTO
   bigquery.ossd.repositories (
      ingestion_time,
      id,
      node_id,
      name_with_owner,
      url,
      name,
      is_fork,
      branch,
      fork_count,
      star_count,
      watcher_count,
      license_spdx_id,
      license_name,
      language,
      _dlt_load_id,
      _dlt_id,
      owner,
      created_at,
      updated_at
   )
VALUES
   (
      current_timestamp - interval '1' day,
      1,
      'node1',
      'owner1/repo1',
      'https://github.com/owner1/repo1',
      'repo1',
      false,
      'main',
      10,
      100,
      50,
      'MIT',
      'MIT License',
      'Python',
      'load1',
      'id1',
      'owner1',
      current_timestamp - interval '1' day,
      current_timestamp
   ),
   (
      current_timestamp - interval '1' day,
      2,
      'node2',
      'owner2/repo2',
      'https://github.com/owner2/repo2',
      'repo2',
      true,
      'main',
      20,
      200,
      100,
      'GPL-3.0',
      'GNU General Public License v3.0',
      'JavaScript',
      'load2',
      'id2',
      'owner2',
      current_timestamp - interval '1' day,
      current_timestamp
   );

CREATE TABLE IF NOT EXISTS bigquery.ossd.sbom (
   artifact_namespace varchar,
   artifact_name varchar,
   artifact_source varchar,
   package varchar,
   package_source varchar,
   package_version varchar,
   snapshot_at timestamp(6) with time zone,
   _dlt_load_id varchar NOT NULL,
   _dlt_id varchar NOT NULL
);

INSERT INTO
   bigquery.ossd.sbom (
      artifact_namespace,
      artifact_name,
      artifact_source,
      package,
      package_source,
      package_version,
      snapshot_at,
      _dlt_load_id,
      _dlt_id
   )
VALUES
   (
      'namespace1',
      'artifact1',
      'source1',
      'package1',
      'source1',
      '1.0.0',
      current_timestamp - interval '1' day,
      'load1',
      'id1'
   ),
   (
      'namespace2',
      'artifact2',
      'source2',
      'package2',
      'source2',
      '2.0.0',
      current_timestamp - interval '1' day,
      'load2',
      'id2'
   );