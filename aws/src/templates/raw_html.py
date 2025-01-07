PASSWORD_RESET_EMAIL_CONTENT = '''
<!DOCTYPE html>
<html>
<head>
    <title>Password Reset Request</title>
</head>
<body>
    <p>Hi <b>{recipient}</b>,</p>
    
    <p> You are receiving this email because you requested a password reset for your GXP account.Your verification code for password reset is::</p>
    
    <p><a href="{reset_link}">Reset Password</a></p>
    
    <p>If you did not request a password reset, please disregard this email. Your password will remain unchanged. If the verification code expires, you can request a new one.</p>
    
    <p>Best regards,</p>
    
    <p>The GXP Team</p>
</body>
</html>
'''
