import winston from "winston";

export const logger = winston.createLogger({
  //level: "info",
  level: "debug",
  format: winston.format.json(),
  defaultMeta: {},
  transports: [
    new winston.transports.Console({
      format: winston.format.json(),
      stderrLevels: ["debug", "info", "warn", "warning", "error"],
    }),
  ],
});
