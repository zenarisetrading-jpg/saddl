/**
 * Netlify Function: Beta Signup Notification
 * 
 * This function is called by a Supabase Database Webhook when
 * a new row is inserted into beta_signups table.
 * 
 * It sends an email notification to the admin.
 */

const nodemailer = require('nodemailer');

exports.handler = async (event, context) => {
    // Only allow POST
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    // Verify webhook secret (optional but recommended)
    const webhookSecret = process.env.WEBHOOK_SECRET;
    const providedSecret = event.headers['x-webhook-secret'] || event.headers['X-Webhook-Secret'];

    if (webhookSecret && providedSecret !== webhookSecret) {
        console.error('Invalid webhook secret');
        return {
            statusCode: 401,
            body: JSON.stringify({ error: 'Unauthorized' })
        };
    }

    try {
        // Parse the webhook payload from Supabase
        const payload = JSON.parse(event.body);

        // Supabase sends the new record in payload.record for INSERT
        const signup = payload.record || payload;

        if (!signup || !signup.email) {
            console.error('Invalid payload:', payload);
            return {
                statusCode: 400,
                body: JSON.stringify({ error: 'Invalid payload' })
            };
        }

        // Create email transporter
        const transporter = nodemailer.createTransport({
            host: process.env.SMTP_HOST,
            port: parseInt(process.env.SMTP_PORT || '587'),
            secure: process.env.SMTP_PORT === '465', // true for 465, false for other ports
            auth: {
                user: process.env.SMTP_USER,
                pass: process.env.SMTP_PASS
            }
        });

        // Format the email
        const emailHtml = `
            <h2>🎉 New Beta Signup Request</h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Name</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${signup.name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Email</td>
                    <td style="padding: 8px; border: 1px solid #ddd;"><a href="mailto:${signup.email}">${signup.email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Role</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${signup.role || 'Not specified'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Accounts Managed</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${signup.accounts || 'Not specified'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Monthly Spend</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${signup.monthly_spend || 'Not specified'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Goal</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${signup.goal || 'Not specified'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Signed Up</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${new Date(signup.created_at || Date.now()).toLocaleString()}</td>
                </tr>
            </table>
            <p style="margin-top: 20px; color: #666;">
                <a href="https://supabase.com/dashboard">View in Supabase Dashboard</a>
            </p>
        `;

        // Send the email
        await transporter.sendMail({
            from: process.env.SMTP_FROM || process.env.SMTP_USER,
            to: process.env.NOTIFICATION_EMAIL || 'aslam.yousuf@saddl.io',
            subject: `[AdPulse Beta] New Signup: ${signup.name}`,
            html: emailHtml,
            text: `New Beta Signup\n\nName: ${signup.name}\nEmail: ${signup.email}\nRole: ${signup.role}\nAccounts: ${signup.accounts}\nSpend: ${signup.monthly_spend}\nGoal: ${signup.goal}`
        });

        console.log('Notification email sent for:', signup.email);

        return {
            statusCode: 200,
            body: JSON.stringify({ success: true, message: 'Notification sent' })
        };

    } catch (error) {
        console.error('Error sending notification:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Failed to send notification', details: error.message })
        };
    }
};
