export class DuneCSVUploader {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async upload(tableName: string, description: string, rows: string[]) {
    return await fetch("https://api.dune.com/api/v1/table/upload/csv", {
      method: "POST",
      body: JSON.stringify({
        table_name: tableName,
        description: description,
        data: rows.join("\n"),
      }),
      headers: {
        "Content-Type": "application/json",
        "X-Dune-Api-Key": this.apiKey,
      },
    });
  }
}
