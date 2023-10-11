-- Gives the progress of the indexer. 
--
-- 
-- If you happen to see that the progress value is GREATER than the expected
-- value then the indexer has event pointers in disparate time ranges.
-- Eventually this will fix itself but a collector could be very very slow.
with expected_by_type as (
	select a."type", count(distinct a.id) as "count"
	from project p
	left join
		project_artifacts_artifact paa 
		on paa."projectId" = p.id
	left join artifact a
		on paa."artifactId" = a.id
	group by a."type"
), event_pointers_progress as (
	select 
		ep.collector as collector,
		case 
			when SPLIT_PART(ep.collector, '-', 1) = 'github' then 'GIT_REPOSITORY'
			when SPLIT_PART(ep.collector, '-', 1) = 'npm' then 'NPM_PACKAGE'
		end as category,
		count(*) as progress
	from event_pointer ep
	-- Move this end date around to see the state of the collectors
	where ep."endDate" > '2023-10-01'
		  and ep."startDate" < '2008-01-01'
	group by
		ep.collector
)
select 
	epp."collector",
	epp."progress",
	ebt."count" as expected
from event_pointers_progress epp
inner join expected_by_type ebt on ebt."type" = cast(epp.category as artifact_type_enum)