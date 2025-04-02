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