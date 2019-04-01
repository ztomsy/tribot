-- curl -X PUT -d '{"deal-uuid": "5df93cc9-efc5-4d17-b92e-4da1bfdaf755","symbol":"QKC/BTC", "start_cur":"QKC", "dest_cur":"BTC", "start_amount":11513.0, "best_dest_amount": 0.103707, "leg":3, "timestamp":123454556  }' "http://localhost:8080/order/"

-- leg2 recover request

select concat('curl -X PUT -d ''{"deal-uuid":' , "dr"."deal_data"->'deal-uuid',',',
'"symbol":', "dr"."deal_data"->'symbol1',',',
'"start_cur":', "dr"."deal_data"->'cur2',',',
'"dest_cur":', "dr"."deal_data"->'cur1',',',
'"start_amount":', "dr"."deal_data"->'leg2-recover-amount',',',
'"best_dest_amount":', "dr"."deal_data"->'leg2-recover-target',',',
'"leg":2', '}'' "http://localhost:8080/order/"'


) from deal_reports as "dr"  where dr.deal_uuid = '8fa1ebbb-9fb4-4afd-9e78-2c2dd193194e' and dr.status in ('OK', 'InRecovery');

-- leg3 recover request

select concat('curl -X PUT -d ''{"deal-uuid":' , "dr"."deal_data"->'deal-uuid',',',
'"symbol":', "dr"."deal_data"->'symbol3',',',
'"start_cur":', "dr"."deal_data"->'cur3',',',
'"dest_cur":', "dr"."deal_data"->'cur1',',',
'"start_amount":', "dr"."deal_data"->'leg3-recover-amount',',',
'"best_dest_amount":', "dr"."deal_data"->'leg3-recover-target',',',
'"leg":3', '}'' "http://localhost:8080/order/"'


) from deal_reports as "dr"  where dr.deal_uuid = '8fa1ebbb-9fb4-4afd-9e78-2c2dd193194e' and dr.status in ('OK', 'InRecovery');

