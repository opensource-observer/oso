/* eslint-disable @next/next/no-img-element */
import { logger } from "@/lib/logger";
import { ImageResponse } from "@vercel/og";
import { NextRequest } from "next/server";

export const runtime = "edge";

async function loadGoogleFont(
  font: string,
  text: string,
  weight: number = 400,
) {
  const url = `https://fonts.googleapis.com/css2?family=${font}:wght@${weight}&text=${encodeURIComponent(
    text,
  )}`;
  const css = await (await fetch(url)).text();
  const resource = css.match(
    /src: url\((.+)\) format\('(opentype|truetype)'\)/,
  );

  if (resource) {
    const response = await fetch(resource[1]);
    if (response.status == 200) {
      return await response.arrayBuffer();
    }
  }

  throw new Error("failed to load font data");
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);

    const orgName = searchParams.get("org") ?? "opensource-observer";
    const notebookName = searchParams.get("notebook") ?? "notebook";
    const description =
      searchParams.get("description") ??
      "Interactive data analysis and visualization";
    const authorAvatar =
      searchParams.get("avatar") ??
      "https://avatars.githubusercontent.com/u/145079657?s=200&v=4";
    const likes = searchParams.get("likes") ?? "1";
    const forks = searchParams.get("forks") ?? "0";

    const logoUrl =
      "https://avatars.githubusercontent.com/u/145079657?s=200&v=4";

    const pawsText = `${likes} Paw${likes === "1" ? "" : "s"}`;
    const forksText = `${forks} Fork${forks === "1" ? "" : "s"}`;

    const allText = `${orgName}/${notebookName}${description}1 Contributor${pawsText}${forksText}`;
    const statsText = `Contributors${likes}Paws${forks}Forks`;

    return new ImageResponse(
      (
        <div tw="h-full w-full flex bg-white font-sans relative">
          <div tw="flex w-full pt-20 pb-10 px-12 justify-between items-start">
            <div tw="flex flex-col max-w-2xl">
              <div tw="flex flex-wrap text-6xl text-gray-900 mb-6 leading-tight">
                <span tw="font-normal">{orgName}/</span>
                <span tw="font-bold">{notebookName}</span>
              </div>

              <div tw="text-3xl text-gray-600 mb-12 leading-normal flex">
                {description}
              </div>
            </div>

            <div tw="flex items-center justify-center pt-10">
              <img
                src={authorAvatar}
                width="240"
                height="240"
                tw="rounded-3xl"
                alt="Author avatar"
              />
            </div>
          </div>

          <div
            style={{
              position: "absolute",
              bottom: 80,
              left: 48,
              display: "flex",
              gap: 64,
              alignItems: "center",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <svg width="28" height="28" viewBox="0 0 16 16" fill="#374151">
                <path d="M1 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"></path>
              </svg>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 20,
                    color: "#6B7280",
                    fontFamily: "Roboto",
                    fontWeight: 400,
                  }}
                >
                  Contributor{likes === "1" ? "" : "s"}
                </span>
                <span
                  style={{
                    fontSize: 32,
                    color: "#1F2937",
                    fontFamily: "Inter",
                    fontWeight: 700,
                  }}
                >
                  1
                </span>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <svg
                stroke="currentColor"
                fill="currentColor"
                strokeWidth="0"
                viewBox="0 0 512 512"
                height="28px"
                width="28px"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M256 224c-79.41 0-192 122.76-192 200.25 0 34.9 26.81 55.75 71.74 55.75 48.84 0 81.09-25.08 120.26-25.08 39.51 0 71.85 25.08 120.26 25.08 44.93 0 71.74-20.85 71.74-55.75C448 346.76 335.41 224 256 224zm-147.28-12.61c-10.4-34.65-42.44-57.09-71.56-50.13-29.12 6.96-44.29 40.69-33.89 75.34 10.4 34.65 42.44 57.09 71.56 50.13 29.12-6.96 44.29-40.69 33.89-75.34zm84.72-20.78c30.94-8.14 46.42-49.94 34.58-93.36s-46.52-72.01-77.46-63.87-46.42 49.94-34.58 93.36c11.84 43.42 46.53 72.02 77.46 63.87zm281.39-29.34c-29.12-6.96-61.15 15.48-71.56 50.13-10.4 34.65 4.77 68.38 33.89 75.34 29.12 6.96 61.15-15.48 71.56-50.13 10.4-34.65-4.77-68.38-33.89-75.34zm-156.27 29.34c30.94 8.14 65.62-20.45 77.46-63.87 11.84-43.42-3.64-85.21-34.58-93.36s-65.62 20.45-77.46 63.87c-11.84 43.42 3.64 85.22 34.58 93.36z"></path>
              </svg>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 20,
                    color: "#6B7280",
                    fontFamily: "Roboto",
                    fontWeight: 400,
                  }}
                >
                  Paw{likes === "1" ? "" : "s"}
                </span>
                <span
                  style={{
                    fontSize: 32,
                    color: "#1F2937",
                    fontFamily: "Inter",
                    fontWeight: 700,
                  }}
                >
                  {likes}
                </span>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <svg width="28" height="28" viewBox="0 0 16 16" fill="#374151">
                <path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"></path>
              </svg>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 20,
                    color: "#6B7280",
                    fontFamily: "Roboto",
                    fontWeight: 400,
                  }}
                >
                  Fork{forks === "1" ? "" : "s"}
                </span>
                <span
                  style={{
                    fontSize: 32,
                    color: "#1F2937",
                    fontFamily: "Inter",
                    fontWeight: 700,
                  }}
                >
                  {forks}
                </span>
              </div>
            </div>
          </div>

          <div tw="absolute bottom-6 right-6 flex">
            <img
              src={logoUrl}
              width="96"
              height="96"
              tw="rounded-xl"
              alt="OSO Logo"
            />
          </div>
        </div>
      ),
      {
        width: 1200,
        height: 630,
        fonts: [
          {
            name: "Inter",
            data: await loadGoogleFont("Inter", allText, 400),
            style: "normal",
            weight: 400,
          },
          {
            name: "Inter",
            data: await loadGoogleFont("Inter", allText, 700),
            style: "normal",
            weight: 700,
          },
          {
            name: "Roboto",
            data: await loadGoogleFont("Roboto", statsText, 400),
            style: "normal",
            weight: 400,
          },
        ],
      },
    );
  } catch (e) {
    logger.error("Failed to generate OG image:", e);
    return new Response(`Failed to generate the image`, {
      status: 500,
    });
  }
}
