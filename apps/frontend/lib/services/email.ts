import mailjet from "node-mailjet";
import {
  DOMAIN,
  MAILJET_API_KEY,
  MAILJET_API_SECRET,
} from "@/apps/frontend/lib/config";

const client = mailjet.apiConnect(MAILJET_API_KEY, MAILJET_API_SECRET);

export interface InvitationEmailData {
  to: string;
  orgName: string;
  inviteToken: string;
  inviterName?: string;
}

export async function sendInvitationEmail({
  to,
  orgName,
  inviteToken,
  inviterName,
}: InvitationEmailData): Promise<void> {
  const PROTOCOL = DOMAIN.includes("localhost") ? "http" : "https";
  const inviteUrl = `${PROTOCOL}://${DOMAIN}/invite/${inviteToken}`;

  const subject = `${
    inviterName || "Someone"
  } invited you to join ${orgName} on OSO`;

  const htmlBody = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>You're invited to ${orgName}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #000000; background-color: #ffffff;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; padding: 60px 20px;">
        <tr>
          <td align="center">
            <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff;">

              <!-- Header -->
              <tr>
                <td style="padding: 0 0 40px 0; text-align: center; border-bottom: 1px solid #000000;">
                  <h1 style="color: #000000; margin: 0; font-size: 24px; font-weight: 400; letter-spacing: 2px;">
                    OSO
                  </h1>
                </td>
              </tr>

              <!-- Main Content -->
              <tr>
                <td style="padding: 40px 0;">
                  <p style="font-size: 16px; margin: 0 0 30px; color: #000000; text-align: center;">
                    You have been invited to join <strong>${orgName}</strong>
                  </p>

                  <p style="font-size: 14px; margin: 0 0 40px; color: #666666; line-height: 1.6; text-align: center;">
                    ${inviterName || "Someone"} has invited you to collaborate on open source analytics and insights.
                  </p>

                  <!-- CTA Button -->
                  <div style="text-align: center; margin: 40px 0;">
                    <a href="${inviteUrl}"
                       style="display: inline-block; background: #000000 !important; color: #ffffff !important; text-decoration: none; padding: 12px 24px; font-weight: 400; font-size: 14px; letter-spacing: 1px; text-transform: uppercase;">
                      Accept Invitation
                    </a>
                  </div>

                  <p style="font-size: 12px; color: #999999; margin: 40px 0 0; line-height: 1.5; text-align: center;">
                    Or visit: ${inviteUrl}
                  </p>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="padding: 30px 0 0; text-align: center; border-top: 1px solid #eeeeee;">
                  <p style="margin: 0 0 10px; font-size: 12px; color: #999999;">
                    This invitation expires in 7 days
                  </p>
                  <p style="margin: 0; font-size: 11px; color: #cccccc; letter-spacing: 1px;">
                    OSO — OPEN SOURCE OBSERVER
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
  `;

  const request = client.post("send", { version: "v3.1" }).request({
    Messages: [
      {
        From: {
          Email: `no-reply@opensource.observer`,
          Name: "OSO - Open Source Observer",
        },
        To: [
          {
            Email: to,
            Name: to,
          },
        ],
        Subject: subject,
        HtmlPart: htmlBody,
      },
    ],
  });

  console.log(JSON.stringify((await request).body, null, 2));
}
