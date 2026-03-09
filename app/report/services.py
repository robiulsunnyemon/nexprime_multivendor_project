from fastapi import HTTPException, status, BackgroundTasks
from app.database.db import prisma
from app.report.schemas import MarketingProductReportCreate, ReportStatus
from app.core.send_email import send_email
from app.core.config import settings


class ReportService:

    @staticmethod
    async def create_report(report_data: MarketingProductReportCreate):
        """Allows a Customer to report another Customer's MarketingProduct."""

        # Check if Reporter and Target are the same person
        if report_data.reporterUserId == report_data.targetUserId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot report yourself."
            )

        # Check if Reporter user exists
        reporter = await prisma.user.find_unique(where={"id": report_data.reporterUserId})
        if not reporter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporter user not found."
            )

        # Check if Target user exists
        target = await prisma.user.find_unique(where={"id": report_data.targetUserId})
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found."
            )

        # Check if MarketingProduct exists
        product = await prisma.marketingproduct.find_unique(where={"id": report_data.marketingProductId})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Marketing product not found."
            )

        # Create the report
        report = await prisma.marketingproductreport.create(
            data={
                "content": report_data.content,
                "reporterUserId": report_data.reporterUserId,
                "targetUserId": report_data.targetUserId,
                "marketingProductId": report_data.marketingProductId,
            },
            include={
                "reporter": True,
                "target": True,
                "marketingProduct": True,
            }
        )
        return report

    @staticmethod
    async def get_all_reports():
        """Fetch all reports (Admin only)."""
        reports = await prisma.marketingproductreport.find_many(
            include={
                "reporter": True,
                "target": True,
                "marketingProduct": True,
            },
            order={"createdAt": "desc"},
            where={"status": ReportStatus.PENDING}
        )
        return reports

    @staticmethod
    async def get_report_by_id(report_id: int):
        """Fetch a specific report by ID."""
        report = await prisma.marketingproductreport.find_unique(
            where={"id": report_id},
            include={
                "reporter": True,
                "target": True,
                "marketingProduct": True,
            }
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found."
            )
        return report

    @staticmethod
    async def admin_update_report_status(
        report_id: int,
        new_status: ReportStatus,
        background_tasks: BackgroundTasks
    ):
        """
        Admin updates report status.
        - DISMISSED -> Report is deleted.
        - REVIEWED  -> Target user becomes INACTIVE + Email notification sent.
        """
        report = await prisma.marketingproductreport.find_unique(
            where={"id": report_id},
            include={
                "reporter": True,
                "target": True,
                "marketingProduct": True,
            }
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found."
            )

        if new_status == ReportStatus.DISMISSED:
            # Delete the report
            await prisma.marketingproductreport.delete(where={"id": report_id})
            return {"detail": "The report has been successfully dismissed and removed."}

        elif new_status == ReportStatus.REVIEWED:
            # Set Target user account to INACTIVE
            await prisma.user.update(
                where={"id": report.targetUserId},
                data={"status": "INACTIVE"}
            )

            # Update report (status and action)
            updated_report = await prisma.marketingproductreport.update(
                where={"id": report_id},
                data={
                    "status": "REVIEWED",
                    "action": "ACCOUNT_INACTIVE",
                },
                include={
                    "reporter": True,
                    "target": True,
                    "marketingProduct": True,
                }
            )

            # Send Email notification via Background Task
            target_email = report.target.email
            support_email = settings.EMAIL_FROM

            def send_inactive_email():
                subject = "Your Nexprime Account Has Been Deactivated"
                body = f"""
Dear {report.target.fullname},

A marketing product report against your Nexprime account has been reviewed by our administration.

Report Content:
"{report.content}"

Based on this report, your account has been set to **Inactive**.

If you believe this decision was made in error or would like to appeal, 
please reply directly to this email: {support_email}

We will review your appeal and notify you of our decision.

Regards,
Nexprime Support Team
                """
                import smtplib
                from email.mime.text import MIMEText
                from app.core.config import settings as cfg

                msg = MIMEText(body, "plain", "utf-8")
                msg["Subject"] = subject
                msg["From"] = cfg.EMAIL_FROM
                msg["To"] = target_email

                try:
                    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT) as server:
                        server.starttls()
                        server.login(cfg.EMAIL_FROM, cfg.SMTP_PASS)
                        server.sendmail(cfg.EMAIL_FROM, target_email, msg.as_string())
                    print(f"Inactive notification email sent to {target_email}")
                except Exception as e:
                    print(f"Failed to send email: {e}")

            background_tasks.add_task(send_inactive_email)

            return updated_report

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Only DISMISSED or REVIEWED are allowed."
            )