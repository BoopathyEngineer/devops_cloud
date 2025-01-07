COUPON_EMAIL = '''
<!DOCTYPE html>
<html>
<head>
<title></title>
</head>
 
<body>
<table style="width: 100%; border-spacing: 0px; font-family: Calibri, sans-serif;">
  <tr>
    <td style="background: #581845;" colspan="3">
      <img style="display: block; margin-left: auto; margin-right: auto;" src="https://d2uv78z986v35y.cloudfront.net/new_zita_white.png"
        width="90" alt="Zita Logo">
    </td>
  </tr>
  
  <tr>
    <td colspan="3">
      <div style="background-color: #ffffff; border-radius: 8px; border: 1px solid rgba(0, 0, 0, 0.1); padding: 22px 35px; margin: 30px 10px 30px 10px;">
        <p style="font-size: 14px; color:black; font-family: Calibri,sans-serif;">Hi {username},</p>
       
        <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;">
          We're excited to offer you an exclusive discount for your next API product or add-on service purchase on Zita!
        </p>
        
        <b><p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;">
          Your Coupon Code:
          <br>
          PromoAPI
        </p></b>
        
        <b><p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"> 
        Coupon Details:</p></b>
       
        <ul>
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"><b>Discount:</b> {discount_value_str} on API products
            </p>
          </li>
          
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"><b>Valid For:</b> API product purchases only
            </p>
          </li>
          
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"><b>Expiry Date:</b> {expiredate}</p>
          </li>
          
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"><b>Minimum Purchase:</b>{minvalue}</p>
          </li>
        </ul>
      
        <b><p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"> 
        How to Use Your Coupon:</p></b>
        
        <ol>
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;">Add an <b>API product</b> to your cart.</p>
          </li>
          
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;">At checkout, enter the coupon code <b>{coupon_code}</b> in the "Coupon Code" field.</p>
          </li>
          
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;">Watch your discount apply instantly!</p>
          </li>
        </ol>
      
        <b><p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"> 
        Important Information:</p></b>
        
        <ul>
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"><b>{coupon_code}</b> is valid for <b>API products only</b> and cannot be used for add-on services.</p>
          </li>
          
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;">This code is valid only once per user.</p>
          </li>
          
          <li>
            <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;">Make sure to use your coupon before it expires on <b>{expiredate}</b>.</p>
          </li>
        </ul>
      
        <p style="color:black; font-family: Calibri,sans-serif; font-size: 14px; text-align: left;"> 
        <b>Need Help?</b>
        <br>If you encounter any issues while applying your coupon, feel free to contact our support team 
        at <a href="mailto:support@zita.ai">support@zita.ai</a>.</p>
        
        <p style="font-size: 14px; font-family: Calibri,sans-serif; text-align: left; color: black;">
          Happy shopping! 
          <br>
          <b>The Zita API Team</b>
        </p>
      </div>
    </td>
  </tr>
 
  <tr>
    <td colspan="2">
      <div style="background-color: #581845;">
        <div style="font-size: 14px; font-family: Calibri,sans-serif; text-align: center; padding-top: 20px; padding-bottom: 10px; color: white;">
          Need help? Ask at <a href="mailto:support@zita.ai" style="color: #fcc203;">support@zita.ai</a> or visit
          our <a href="https://www.zita.ai/knowledgebase" style="color: #fcc203;">Help Center</a>
        </div>
 
        <div style="font-size: 14px; font-family: Roboto; text-align: center; line-height: 16.41px; padding-bottom: 20px; padding-top: 10px; color: white; font-weight: 400;">
            Sense7ai Inc,<br>
            Corporate Commons,<br>
            6200 Stoneridge Mall Road, Suite 300, Pleasanton, CA, USA, 94588
        </div>
 
        <div style="text-align: center; padding-bottom: 20px;">
          <a href="https://twitter.com/ai_zita"><img src="https://zita2.s3.us-east-2.amazonaws.com/twitter.png"
          width="16" height="16" alt="Twitter" style="border-radius: 4px;"></a>
          <a href="https://www.linkedin.com/company/zita-ai/"><img src="https://zita2.s3.us-east-2.amazonaws.com/linkedin.png" width="16" height="16" alt="LinkedIn"></a>
          <a href="https://www.youtube.com/channel/UCSjD_inAzR9Z4sMwFJJgUWA"><img src="https://d2uv78z986v35y.cloudfront.net/youtube.png" width="16" height="16" alt="YouTube"></a>
        </div>
      </div>
    </td>
  </tr>
</table>
</body>
</html>
'''
