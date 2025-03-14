CREATE SCHEMA IF NOT EXISTS bigquery.oso;

CREATE TABLE IF NOT EXISTS bigquery.oso.int_events__blockchain (
   time timestamp(6) with time zone,
   to_artifact_id varchar,
   from_artifact_id varchar,
   event_type varchar,
   event_source_id varchar,
   event_source varchar,
   to_artifact_name varchar,
   to_artifact_namespace varchar,
   to_artifact_type varchar,
   to_artifact_source_id varchar,
   from_artifact_name varchar,
   from_artifact_namespace varchar,
   from_artifact_type varchar,
   from_artifact_source_id varchar,
   amount double
);

INSERT INTO
   bigquery.oso.int_events__blockchain
VALUES
   (
      current_timestamp - interval '2' day,
      'artifact1',
      'artifact2',
      'type1',
      'source1',
      'sourceA',
      'name1',
      'namespace1',
      'typeA',
      'sourceID1',
      'name2',
      'namespace2',
      'typeB',
      'sourceID2',
      100.0
   ),
   (
      current_timestamp - interval '1' day,
      'artifact3',
      'artifact4',
      'type2',
      'source2',
      'sourceB',
      'name3',
      'namespace3',
      'typeC',
      'sourceID3',
      'name4',
      'namespace4',
      'typeD',
      'sourceID4',
      200.0
   );

CREATE TABLE IF NOT EXISTS bigquery.oso.stg_deps_dev__dependencies (
   snapshotat timestamp(6) with time zone,
   system varchar,
   name varchar,
   version varchar,
   dependency ROW(System varchar, Name varchar, Version varchar),
   minimumdepth bigint
);

INSERT INTO
   bigquery.oso.stg_deps_dev__dependencies
VALUES
   (
      current_timestamp - interval '2' day,
      'system1',
      'name1',
      '1.0',
      ROW('systemA', 'nameA', '1.0'),
      1
   ),
   (
      current_timestamp - interval '1' day,
      'system2',
      'name2',
      '2.0',
      ROW('systemB', 'nameB', '2.0'),
      2
   );

CREATE TABLE IF NOT EXISTS bigquery.oso.stg_deps_dev__packages (
   snapshotat timestamp(6) with time zone,
   system varchar,
   projectname varchar,
   name varchar,
   version varchar
);

INSERT INTO
   bigquery.oso.stg_deps_dev__packages
VALUES
   (
      current_timestamp - interval '2' day,
      'system1',
      'owner/repo/project1',
      'name1',
      '1.0'
   ),
   (
      current_timestamp - interval '1' day,
      'system2',
      'owner/repo/project2',
      'name2',
      '2.0'
   );

CREATE TABLE IF NOT EXISTS bigquery.oso.stg_github__events (
   type varchar,
   public boolean,
   payload varchar,
   repo ROW(id bigint, name varchar, url varchar),
   actor ROW(
      id bigint,
      login varchar,
      gravatar_id varchar,
      avatar_url varchar,
      url varchar
   ),
   org ROW(
      id bigint,
      login varchar,
      gravatar_id varchar,
      avatar_url varchar,
      url varchar
   ),
   created_at timestamp(6) with time zone,
   id varchar,
   other varchar
);

INSERT INTO
   bigquery.oso.stg_github__events
VALUES
   (
      'type1',
      true,
      'payload1',
      ROW(1, 'repo1', 'url1'),
      ROW(1, 'login1', 'gravatar1', 'avatar1', 'url1'),
      ROW(1, 'login1', 'gravatar1', 'avatar1', 'url1'),
      current_timestamp - interval '2' day,
      'id1',
      'other1'
   ),
   (
      'type2',
      false,
      'payload2',
      ROW(2, 'repo2', 'url2'),
      ROW(2, 'login2', 'gravatar2', 'avatar2', 'url2'),
      ROW(2, 'login2', 'gravatar2', 'avatar2', 'url2'),
      current_timestamp - interval '1' day,
      'id2',
      'other2'
   );