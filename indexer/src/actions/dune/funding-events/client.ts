/**
 * A client for our daily contract usage query on Dune
 *
 * The client will resolve everything in the request to raw addresses as we
 * currently use a method for querying dune that involves passing in
 * known-user-addresses + ids and known-contract-addresses + ids. This reduces
 * the burden of the api calls on our quota by about 20% in testing.
 */
import { DateTime } from "luxon";
import { QueryParameter } from "@cowprotocol/ts-dune-client";

import { IDuneClient } from "../../../utils/dune/type.js";
import { Cacheable } from "../../../cacher/time-series.js";
import { logger } from "../../../utils/logger.js";
import { writeFile } from "fs/promises";

export type FundingEventRawRow = {
  block_time: string;
  from: string;
  to: string;
  blockchain: string;
  token: string;
  value: string;
  tx_hash: string;

  // Catch all for other raw values returned in the result
  [key: string]: any;
};

export type FundingEventRow = {
  blockTime: string;
  from: string;
  to: string;
  blockchain: string;
  token: string;
  value: string;
  txHash: string;

  // Catch all for other raw values returned in the result
  [key: string]: any;
};

export type FundingPoolAddress = {
  id: number;
  groupId: number;
  address: string;
};

export type ProjectAddress = {
  id: number;
  projectId: number;
  address: string;
};

export interface IFundingEventsClient {
  getFundingEvents(
    start: DateTime,
    end: DateTime,
    fundingPoolAddresses: FundingPoolAddress[],
    projectAddresses: ProjectAddress[],
  ): Promise<Cacheable<FundingEventRow[], string>>;
}

export interface FundingEventsClientOptions {
  queryId: number;
}

export const DefaultFundingEventsClientOptions: FundingEventsClientOptions = {
  // This default is based on this: https://dune.com/queries/3020253
  queryId: 3020253,
};

export class FundingEventsClient implements IFundingEventsClient {
  private client: IDuneClient;
  private options: FundingEventsClientOptions;

  constructor(
    client: IDuneClient,
    options: FundingEventsClientOptions = DefaultFundingEventsClientOptions,
  ) {
    this.client = client;
    this.options = options;
  }

  /**
   * Refreshes the dune [query](https://dune.com/queries/3020253)
   *
   * @param start
   * @param end
   * @param fundingPoolAddresses
   * @param projectAddresses
   */
  async getFundingEvents(
    start: DateTime,
    end: DateTime,
    fundingPoolAddresses: FundingPoolAddress[],
    projectAddresses: ProjectAddress[],
  ): Promise<Cacheable<FundingEventRow[], string>> {
    logger.debug("Calling dune for funding events");
    const projectAddressesInput = projectAddresses.map((a) => {
      return `(${a.id}, ${a.projectId}, ${a.address})`;
    });
    const fundingPoolAddressesInput = fundingPoolAddresses.map((a) => {
      return `(${a.id}, ${a.groupId}, ${a.address})`;
    });

    const parameters = [
      QueryParameter.text("project_addresses", projectAddressesInput.join(",")),
      QueryParameter.text(
        "funding_pool_addresses",
        fundingPoolAddressesInput.join(","),
      ),
      QueryParameter.text(
        "start_time",
        start.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
      ),
      QueryParameter.text(
        "end_time",
        end.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
      ),
    ];

    const response = await this.client.refresh(
      this.options.queryId,
      parameters,
    );
    const rawRows = response.result?.rows || [];
    const rows: FundingEventRow[] = rawRows.map((r) => {
      const raw = r as FundingEventRawRow;
      return {
        blockTime: DateTime.fromSQL(raw.block_time).toISO() || "",
        from: raw.from,
        to: raw.to,
        blockchain: raw.blockchain,
        token: raw.token,
        value: raw.value,
        txHash: raw.tx_hash,
      };
    });
    return {
      raw: rows,
      cacheRange: {
        startDate: start,
        endDate: end,
      },
      hasNextPage: false,
    };
  }
}
