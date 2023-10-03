import { normalizeToObject } from "../utils/common.js";
import { AppDataSource } from "./data-source.js";
import type { Brand } from "utility-types";
import { EventPointer, Event } from "./orm-entities.js";

export const EventPointerRepository = AppDataSource.getRepository(
  EventPointer,
).extend({
  async getPointer<PointerType>(
    artifactId: Brand<number, "ArtifactId">,
    collector: string,
  ) {
    const record = await this.findOne({
      relations: {
        artifact: true,
      },
      where: {
        artifact: {
          id: artifactId,
        },
        collector: collector,
      },
    });
    if (!record) {
      return null;
    }
    // Safe because `Partial` means they're all optional props anyway
    return normalizeToObject<PointerType>(record);
  },
});

export const EventRepository = AppDataSource.getRepository(Event);
