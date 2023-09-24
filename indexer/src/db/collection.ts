import { AppDataSource } from "./data-source.js";
import { Collection } from "./orm-entities.js";

export const CollectionRepository = AppDataSource.getRepository(Collection);
