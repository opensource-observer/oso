import winston from "winston";

const logFormat = winston.format.printf(function (info) {
  const date = new Date().toISOString();
  return `[${info.level}] ${date}: ${JSON.stringify(info.message, null, 2)}`;
});

export const logger = winston.createLogger({
  //level: "info",
  level: "debug",
  format: winston.format.json(),
  defaultMeta: {},
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(winston.format.colorize(), logFormat),
      stderrLevels: ["debug", "info", "warn", "warning", "error"],
    }),
    //new winston.transports.File({ filename: "error.log", level: "error" }),
    //new winston.transports.File({ filename: "combined.log", level: "info" }),
  ],
});
