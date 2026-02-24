import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const AMAZON_TOKEN_URL = "https://api.amazon.com/auth/o2/token";
const STREAMLIT_APP_URL = "https://saddle-adpulse.streamlit.app";

serve(async (req) => {
  const url = new URL(req.url);
  const code = url.searchParams.get("spapi_oauth_code");
  const state = url.searchParams.get("state"); // this will be the client_id
  const error = url.searchParams.get("error");

  // Handle Amazon returning an error
  if (error) {
    return Response.redirect(`${STREAMLIT_APP_URL}?amazon_auth=failed&reason=${error}`);
  }

  if (!code || !state) {
    return new Response("Missing code or state parameter", { status: 400 });
  }

  // Exchange auth code for refresh token
  const tokenResponse = await fetch(AMAZON_TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code: code,
      redirect_uri: "https://wuakeiwxkjvhsnmkzywz.supabase.co/functions/v1/amazon-oauth-callback",
      client_id: Deno.env.get("LWA_CLIENT_ID")!,
      client_secret: Deno.env.get("LWA_CLIENT_SECRET")!,
    }),
  });

  if (!tokenResponse.ok) {
    const err = await tokenResponse.text();
    console.error("Token exchange failed:", err);
    return Response.redirect(`${STREAMLIT_APP_URL}?amazon_auth=failed&reason=token_exchange`);
  }

  const tokens = await tokenResponse.json();
  const refreshToken = tokens.refresh_token;

  // Store in Supabase
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const { error: dbError } = await supabase
    .from("client_settings")
    .upsert({
      client_id: state,
      lwa_refresh_token: refreshToken,
      onboarding_status: "connected",
      updated_at: new Date().toISOString(),
    }, { onConflict: "client_id" });

  if (dbError) {
    console.error("DB write failed:", dbError);
    return Response.redirect(`${STREAMLIT_APP_URL}?amazon_auth=failed&reason=db_error`);
  }

  // Success — send them back to Streamlit
  return Response.redirect(`${STREAMLIT_APP_URL}?amazon_auth=success&client_id=${state}`);
});
