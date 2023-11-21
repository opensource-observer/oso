//import winston from "winston";

export const logger = console;
/**
export const logger = winston.createLogger({
  //level: "info",
  level: "debug",
  format: winston.format.json(),
  defaultMeta: {},
  transports: [
    new winston.transports.Console({
      format: winston.format.printf(
        (info) => `${info.message}`,
        //info => `${moment().format("HH:mm:ss")}:${info.level}\t${info.message}`
      ),
      stderrLevels: ["error"],
    }),
    //new winston.transports.File({ filename: "error.log", level: "error" }),
    //new winston.transports.File({ filename: "combined.log", level: "info" }),
  ],
});
*/
