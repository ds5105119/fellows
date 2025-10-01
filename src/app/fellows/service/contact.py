from logging import getLogger

from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from mypy_boto3_sesv2 import SESV2Client

from src.app.fellows.schema.contact import ContactRequest

logger = getLogger(__name__)


def _create_contact_email_body(data: ContactRequest):
    """프로젝트 문의 이메일의 HTML 및 텍스트 본문을 생성합니다."""

    body_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 40px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ color: #333; font-size: 22px; }}
            .content p {{ color: #555; font-size: 15px; line-height: 1.6; margin: 6px 0; }}
            .highlight {{ font-weight: bold; color: #0056b3; }}
            .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>새로운 프로젝트 문의가 도착했습니다.</h1>
            </div>
            <div class="content">
                <p><span class="highlight">이름:</span> {data.name}</p>
                <p><span class="highlight">회사:</span> {data.company or "미입력"}</p>
                <p><span class="highlight">레벨:</span> {data.level or "미입력"}</p>
                <p><span class="highlight">예산:</span> {data.budget}</p>
                <p><span class="highlight">이메일:</span> {data.email}</p>
                <p><span class="highlight">연락처:</span> {data.phone or "미입력"}</p>
                <p><span class="highlight">프로젝트 설명:</span><br>{data.description}</p>
            </div>
            <div class="footer">
                <p>© 2025 Fellows. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    body_text = f"""
    새로운 프로젝트 문의가 도착했습니다.

    이름: {data.name}
    회사: {data.company or "미입력"}
    레벨: {data.level or "미입력"}
    예산: {data.budget}
    이메일: {data.email}
    연락처: {data.phone or "미입력"}
    프로젝트 설명: {data.description}

    © 2025 Fellows
    """

    return body_html, body_text


class ContactService:
    def __init__(
        self,
        ses_client: SESV2Client,
    ):
        self.ses_client = ses_client

    async def send_email(self, to_email: str, subject: str, body_text: str, body_html: str):
        try:
            response = self.ses_client.send_email(
                FromEmailAddress="noreply@iihus.com",
                Destination={"ToAddresses": [to_email]},
                Content={
                    "Simple": {
                        "Subject": {
                            "Data": subject,
                            "Charset": "UTF-8",
                        },
                        "Body": {
                            "Text": {
                                "Data": body_text,
                                "Charset": "UTF-8",
                            },
                            "Html": {
                                "Data": body_html,
                                "Charset": "UTF-8",
                            },
                        },
                    }
                },
            )
            logger.info(f"Email sent via SESv2! Message ID: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"Failed to send email using SESv2: {e.response['Error']['Message']}")
            return False

    async def create_contact(
        self,
        data: ContactRequest,
    ):
        subject = f"새로운 프로젝트 문의 입니다."
        body_html, body_text = _create_contact_email_body(data)

        email_sent = await self.send_email(
            to_email="contact@iihus.com",
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )

        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이메일 발송에 실패했습니다.",
            )
