
-- select triarb deals which were done in current date period  

select count(*) from ( 

select id, "timestamp",timestamp_start, exchange, "instance", "server", deal_type, deal_uuid, status, currency, 
start_amount, result_amount, gross_profit, net_profit, config, deal_data FROM deal_reports 

where deal_uuid in (

	select distinct(deal_uuid) from deal_reports where
	 
	"deal_type" = 'triarb' and "status" in ('OK', 'InRecovery') and
	 
     timestamp > '2019-03-14 00:00:00' and timestamp < '2019-03-15 00:00:00' 
	
	) 

	
)	 as foo 
;