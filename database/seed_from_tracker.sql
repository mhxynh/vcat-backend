-- Seed generated from Controls Tracker CSV (2025 Controls)
-- Mimics spreadsheet rows: one control row -> one request -> two tests (DAT & OET)
\set ON_ERROR_STOP on
BEGIN;

TRUNCATE TABLE
  audit_logs,
  comments,
  tests,
  requests,
  controls,
  users
RESTART IDENTITY CASCADE;

-- ----------------------------
-- USERS (from sheet testers + one manager)
-- ----------------------------
INSERT INTO users (email, role, display_name) VALUES
  ('monique@vcat.local', 'MANAGER'::user_role, 'Monique'),
  ('alan@vcat.local', 'TESTER'::user_role, 'Alan'),
  ('avinash@vcat.local', 'TESTER'::user_role, 'Avinash'),
  ('brendan@vcat.local', 'TESTER'::user_role, 'Brendan'),
  ('clara@vcat.local', 'TESTER'::user_role, 'Clara'),
  ('jahad@vcat.local', 'TESTER'::user_role, 'Jahad'),
  ('jason@vcat.local', 'TESTER'::user_role, 'Jason'),
  ('jen@vcat.local', 'TESTER'::user_role, 'Jen'),
  ('mark@vcat.local', 'TESTER'::user_role, 'Mark'),
  ('michael@vcat.local', 'TESTER'::user_role, 'Michael'),
  ('michel@vcat.local', 'TESTER'::user_role, 'Michel'),
  ('mike@vcat.local', 'TESTER'::user_role, 'Mike'),
  ('sara@vcat.local', 'TESTER'::user_role, 'Sara')
;

-- ----------------------------
-- SOURCE DATA (from tracker)
-- ----------------------------
WITH src (
  ref, vgcpid, title, notes, control_owner, control_sme, escalation,
  assigned_tester_name,
  dat_status, dat_step,
  oet_status, oet_step,
  request_status,
  date_started, due_date, eta, date_completed
) AS (
  VALUES
    (2, 'VGCP-05245', '
Threat reports with identified vulnerabilities are distributed to stakeholders to action upon.', '12-10 AW | Testing assigned
12-19 AW | Per email from Clara, asked CSOC to determine if DAT still valid
12-19 AW | Prework - Sent email to CSOC requesting meeting
01-08 AW | Accepted invitation for 1/13 walkthrough
1/22 CW: WT scheduled for 1/22. In person meeting scheduled for 1/30.
1/30 CW: DAT and OET ready for review
2/5/25 JM - DAT review complete & ready for BP, OET review done with one comment.
2/6 CW: DAT loaded to BP for approval; comment was addressed in OET and back to Javier''s queue
2/7/25 JM - DAT approved in BP, OET secondary review completed, ready for next steps.
2/10 CW: ready for approval in BP
2/10/25 JM - OET approved in BP', 'Dennis', NULL, FALSE, 'Alan', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-01-22', '2025-01-31', '2025-01-24', '2025-02-10'),
    (3, 'VGCP-05603', 'Red Team Exercises are conducted to test and improve detection and prevention capabilities', '1/8/25-Walkthrough scheduled for next Tuesday with Charles S.
1/14-Walkthrough with Charles, due date for evidence set for 1/21
1/22-Partial evidence recieved yesterday, Waiting for remaing evidence from Charles
1/23-Remaining evidence recieved
1/23-DAT In Javiers Review
1/27-OET in progress,waiting for a couple more pieces of evidence to complete test
1/30-OET In Javiers Review
2/5/25 JM - DAT approved in BP, OET review complete, ready for BP upload.
2/5/25-OET Uploaded into BP
2/7/25 JM - OET approved in BP.', 'Charles', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-01-24', '2025-01-31', '2025-01-31', '2025-02-07'),
    (4, 'VGCP-05605', 'Purple Team Exercise are conducted to test and improve detection and prevention capabilities', '1/8/25-Walkthrough scheduled for next Tuesday with Charles S.
1/14-Walkthrough with Charles, due date for evidence set for 1/21
1/22-Partial evidence recieved yesterday, Waiting for remaing evidence from Charles
1/23-Remaining evidence recieved
1/23-DAT In Javiers Review
1/27-OET in progress,waiting for a couple more pieces of evidence to complete test
1/30-OET In Javiers Review
2/5/25 JM - DAT approved in BP, OET review complete, ready for BP upload.
2/5/25-OET Uploaded into BP
2/7/25 JM - OET approved in BP.', 'Charles', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-01-24', '2025-01-31', '2025-01-31', '2025-02-07'),
    (5, 'VGCP-05610', 'Standard Operating Procedures for SIEM monitoring rules and alerts are established through a formal process.', '12-10 AW | Testing assigned
12-19 AW | CSOC REQ2308229 filed
01-08 AW | DAT 22048901 Testing started
01-08 AW | DAT 22048901 Test submitted for review
1/09/25 JM - Review complete, ready for BP.
01-09 AW | DAT 22048901 Test review completed - Ready for BP
01-09 AW | DAT 22048901 Test uploaded in BP
01-09 AW | Evidence requested - due 1/23 | Also meeting scheduled for 1/14 to review unredacted evidence
1/10/25 JM - DAT approved in BP, ready for OET.
1/22 CW: In person meeting scheduled for 1/30.
1/30 CW: In person meeting completed. Awaiting evidence of redacted screenshots for completion of OET.
2/7/25 JM - OET review complete, ready for next steps.
2/10 CW: ready for approval in BP
2/10/25 JM - OET approved in BP', 'Jonathan', NULL, FALSE, 'Alan', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-01-01', '2025-01-31', '2025-01-24', '2025-02-10'),
    (6, 'VGCP-06321', 'All transactions are monitored for fraud and accounts with potential fraud are investigated (Accumulation)', '1/8/2025 walkthru complete.
1/9/2025 DAT in progress and gathering evidence
1/9/2025 receved accumulation alerts. spent time getting up sample and sending sample to AU. Also setup meeting for 1/14/2025 to walkthru alert.
1/10/2025 recvd message from Malcolm saying that this evidence wont be available until end of month. Moving ETA to end of month.
1/10/2025 working on DAT. reaching out to Malcolm with some further questions.
1/13/2025 did not revc answers back reached out again for answers to my questions.
1/14/2025 receved responses to osme questions but not all. awaiting more responses.
1/14/2025 alert walkthru complete
1/16/2025 DAT in review
1/17 CW: DAT reviewed with comments
1/17 MH addressing comments. sent message to AU
1/21 did not get all my questions answered. reached out again
1.21 got answers.
1/22 DAT updated and in review
1/22 OET in review
1/22 CW: DAT is ready for BP. OET is reviewed with comments.
1/22 DAT uploaded to BP waiting approval. Working on OET comments.
1/22 updated OET and submitted OET for review.
1/23 review complete. Uploaded to BP. OET complete.', 'Mason', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-01-16', '2025-01-31', '2025-01-24', '2025-01-23'),
    (8, 'VGCP-08356', 'NEW CONTROL: The Incident Response Plan between Blackrock and Vanguard is reviewed and approved at least annualy for security handling', '7/31/2025 - OET approved in Archer (JWM)
7/31/2025-OET uploaded into Archer
7/30/2025 - OET worksheet reviewed. Ready for Archer (JWM)
7/29/2025-OET in review
7/28/2025-Will start OET on 7/28
7/25/2025 - DAT approved in Archer (JWM)
7/25/2025-DAT uploaded into Archer
7/22/2025 - DAT ready for Archer (JWM)
7/17 - DAT Reviewed. Need to add reporting period, then ready for Archer (JWM)
7/17-DAT in JM/CW review
7/16/25- Blackrock gave their approval Via email. Next Steps: Will send DAT Narrative for review and get evidence from 3SOC
7/15-Blackrock responed to Vicky saying they are making updates to the contact names and information
7/14/2025-Representative from Blackrock responded on 7/11. The person to approve the IR plan was out of office last week, He is back on 7/14 and they will reach out to Vicky on Monday with an update
7/10/2025-On 7/9/25 3SOC sent a follow up email reaching out to BR for their approval of the plan. Archit and I will meet up next week to look over DAT and Evidence he was able to collect. Josh Sowers still needs to look over DAT when he returns from PTO
6/25-On 6/24 Archit sent out a follow up email to Blackrock for their approval of IR plan. Next steps: Gather evidence such as meeting minutes from Acrhit for OET evidence.
6/20/2025-Had a meeting with Archit on 6/18 to discuss evidence needed for test. Vickie Golub has also sent out a follow up email on 6/18 to black rock for their sign off of the plan
6/09/25- Blackrock has responded and mentioned they are updating the contact information on IR plan. They will provide the updated information and approval this week.
5/29/25-Follow up email sent to Blackrock for Approval of plan, No response from Blackrock as of 5/29/25
5/22/25- Update form Archit:No response from Blackrock about approval of IR plan
5/14/25-3SOC sent a follow up email to BlackRock for approval
5/6/2025- 3SOC team reached out to BR for an update on the approval of the IR plan. No response from BR yet.
4/25/25-Blackrock responded: They are waiting for final sign off/approval of the IR plan on their side, they are open to doing a joint TTX and sent a questionarre out to 3SOC team
4/23/25-Reached out to 3SOC team for an update and requested they continue to send reminders/follow up with 3SOC and 4/22/25-Vickie G, reached out to BR for an update 3/30-3SOC has been in contact with BR to schedule a call to review the IR plan. Clara and Jason will be included on call once it is scheduled. Will reach out to 3SOC for another update later this week
1/8/25-Reached out to Jose Passillas for walkthrough. No response yet, will send a follow up
4/14-Blackrock is reviewing IR plan
1/10/25-Follow up email sent to Jose.
1/13/25-Walktrhough sceduled for Wednesday 1/15
1/15/25-Walkthrough with Jose
1/22/25-There are meetings in the upcoming weeks to update this process to align with the process 3socs process.
1/23/25 JM - After meeting with SWIFT PM Vickie G. this task is on hold until further notice to allow 3SOC to complete the setup of their new process.
1/28/25- Meeting with 3soc and all stakeholders took place to discuss the IR process for BR. SOP is being revised and updated. Timeline of 2 weeks was given for SOP to be completed and for ISCA to start testing.
2/4/25- Emailed BR MSA to 3soc
2/14/25- conducted internal tabletop exercise with relevant stakeholders, Will begin to draft Narrative for control
2/19-Will focus on drafting narrartive Thursday and Friday
2/24-Narrative has been drafted up. WIll create new control in BP
3/7/25 JM - DAT narrative reviewed, comments added.
3/10/25-DAT draft in Javiers review
3/17/2025-Making minor edits Clara and I spoke about to draft narrative. Jose showing up as Uknown?
3/20/2025-Meeting on Monday with Josh Sowers to update him on the control and pick up where Jose left off', 'Josh', 'Archit Saxena', FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing In Progress', 'COMPLETED', NULL, '2025-01-31', '2025-07-31', '2025-07-31'),
    (9, 'VGCP-08365', 'NEW CONTROL: A BI-Annual table-top exercise (TTX) is conducted of a secuirty incident notice from Blackrock and action items are documented to adress uncovered gaps', '7/3/25- Cleaned up control and will be repurposed
6/30-This control will be cleaned up and repurposed
6/25-SRA has responded and is okay with using CSOCs June 2024 TTX for this years testing as it falls in line with the every 2 years requirement. Next steps: Reupload Testing of CSOC 2024 TTX
6/20/25-The justification has been sent by Vickie to SRA regarding this control. We will refer them to the CSOC TTX of 2024.
6/4/25-Meeting with CSOC,BCM,ISCA and 3SOC, Everyone involved agreed not to do another TTX in 2025 with BlackRock. We will rely on 2024 evidence during SRA SIWFT audit. 3Soc will prepare justification incase SRA ask questions about BR involvement
5/22/25-3Soc is working with other teams such as BCM,GTO to schedule a large TTX exercise. No target date as of right now but Archit will update me as they work to schedule the TTX
5/7/2025-Cheryl informed me she had a discussion with Josh Sowers about having a joint TTX with BR. Josh has agreed to include BR
4/25/25-Blackrock responed:They are waiting for final sign off/approval of the IR plan on their side, They are open to doing a joint TTX and sent a questionarre out to 3SOC team
4/23/25-Reached out to 3SOC team for an update and requested they continue to send reminders/follow up with 3SOC
4/22/25-Vickie G, reached out to BR for an Update
4/14-Blackrock is reviewing IR plan
3/30-3SOC has been in contact with BR to schedule a call to review the IR plan. Clara and Jason will be included on call once it is schedule. Will reach out to 3SOC for another update later this week.
2/19- Will focus on drafting narrative for table top exercise control Thursday and Friday
2/19-Narrative has been drafted up
3/7/25 JM - DAT narrative reviewed, comments added.
3/17/25-Making minor edits Clara and I spoke about to the narrative. Jose showing up as Unknown?
3/20/25-Meeting on Monday with Josh Sowers to update him on this control and pick up where Jose left off', 'Josh', 'Archit Saxena', FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, 'COMPLETED', NULL, NULL, NULL, NULL),
    (10, 'VGCP-08123', 'NEW CONTROL: All transactions are monitored for fraud and accounts with potential fraud are investigated (Pension)', '1/8/2025 walkthru complete.
1/9/2025 DAT in progress and gathering evidence
1/9/2025 receved accumulation alerts. spent time getting up sample and sending sample to AU. Also setup meeting for 1/14/2025 to walkthru alert.
1/10/2025 recvd message from Malcolm saying that this evidence wont be available until end of month. Moving ETA to end of month.
1/10/2025 working on DAT. reaching out to Malcolm with some further questions.
1/13/2025 did not revc answers back reached out again for answers to my questions.
1/14/2025 receved responses to osme questions but not all. awaiting more responses
1/14/2025 alert walkthru complete
1/16/2025 DAT in review
1/17 CW: DAT reviewed with comments
1/17 MH addressing comments. sent message to AU
1/21 got answers to questions. working on DAT comments.
1/22 DAT updated and in review
1/22/2025 OET in review
1/22 CW: DAT is ready for BP. OET is reviewed with comments.
1/22 DAT uploaded to BP waiting approval. Working on OET comments.
1/23 OET updated and in review
1/23 review complete. OET uploaded to BP. OET complete.', 'Scott, Mason (064291)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-01-08', '2025-01-31', '2025-01-24', '2025-01-23'),
    (11, 'VGCP-08124', 'All suspected fraudulent activity related to the Super Annuation business are documented as cases, further investigated, and elevated as necessary.', '1/23/2025 Walkthru scheduled for 1/28
1/28/2025 walthru moved to 2/3
2/3 walkthru complete
2/3 received evidence
2/4 reached out with question about evidence
2/5/ reached out with another question about evidence
2/6 received response. continuing work on DAT. Still had to reach out with another question.
2/14 met with Malcolm to get questions answered. DAT in review
2/18 CW: DAT reviewed with comments
2/18 meeting with Clara 2/19 for comments.
2/19 reached out with questions to AU
2/20 received anwers to question but had one more question.
2/26 reached out with one more question.
2/28 DAT back in review updated per comments.
3/5 CW: DAT reviewed. I made some changes to the DAT so please review and if accurate, please load to BP.
3/12 DAT uploaded to BP.
3/14 DAT and OET uploaded to BP and approved. Testing complete.', 'Scott, Mason (064291)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-02-28', '2025-03-14', '2025-03-14'),
    (12, 'VGCP-02973', 'CyberArk/ID Vault is used to authorize, limit, and record administrative access for SWIFT deployments.', 'Control Owner: Ryan Sepe; SME: Chris Swartz
2/26 setup follow-up wit IAM for 2/27 for evidence
2/26 2/21 - 2/26 several follow-ups to get missing evidence
4/3 MB - Looking at population from SNOW. Scheduled meeting with Ryan 4/7 on historical infromation for step 4 and configuration evidence for step 6
4/10 - Evidence request out on 4/7
4/16 - OET mostly ocmplete. REQ2441115 sent 4/14 for additional evidence needs; report request escalated to IAM Priv team.
4/23 - Messaged Garima Behal on report creation updates for REQ noted above.
4/24 - Report received. OET testing ETA Friday 4/25.
4/28 - Meeting on 4/29 with SME on a few samples deviating from normal evidence.', 'Sepe, Ryan (181019)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-07', '2025-02-28', '2025-05-09', '2025-04-29'),
    (13, 'VGCP-03623', 'The vulnerability scanning tool is monitored for availability and ability to receive updates', NULL, 'Kushari, Dip (018642)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-03', '2025-02-28', '2025-03-15', '2025-03-13'),
    (14, 'VGCP-03624', 'The vulnerability scanning tool scheduled to routinely scan the environment', NULL, 'Kushari, Dip (018642)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-03', '2025-02-28', '2025-03-15', '2025-03-20'),
    (15, 'VGCP-03626', 'An authentication reconciliation is conducted for the vulnerability scanning tool on a regular basis', 'Control retired', NULL, NULL, FALSE, 'Michel', 'COMPLETED', 'Walkthrough Completed', 'COMPLETED', NULL, 'COMPLETED', '2025-02-03', '2025-02-28', '2025-03-15', '2025-03-07'),
    (16, 'VGCP-03690', 'Credentials used for authenticated vulnerability scanning are protected through CyberArk.', '1/24 reached out to control owner to schedule walkthru
1/29 Walkthru scheduled for 2/7
2/11 evidence request sent due 2/18. updated eta.
2/11 sent request for meeting to Dave B.
2/12 DAT in review
2/18 CW: DAT reviewed with comments
2/18 DAT updated and back in review.
2/20 DAT updated and back in review
2/21 DAT uploaded to BP. Working on OET.
2/21 OET in review
2/26 CW: DAT approved in BP. OET reviewed and ready for BP
2/26 MH OET uploaded to BP. OET complete
2/26 CW: OET approved in BP', 'Sepe, Ryan (181019)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-07', '2025-02-28', '2025-02-26', '2025-02-26'),
    (17, 'VGCP-06771', 'The vulnerability scanning tool scheduled to routinely scan the environment', '3/19 CW: DAT approved in BP
Additional evidence collection requiired 3/17. Awaiting CO response. MB followed up on 3/20; ETA 3/21
OET completed. Few residual questions out to CO 3/25.
3/31 - sent note to delegate on residual questions to complete. 4/1 - sent note; 4/3 spoke, they plan on reviewing on 4/4.
4/10 - Follow up questions on 4/4 from delegate, responded on 4/4; Team is reviewing as of 4/4.
4/15 - Evidence request sent to Matt Jung
4/16 - Spoke w Matt Jung, likely test failure, collecting additional evidence and impact analysis. MB to circle back on 4/21 for status.
4/23 - Spoke with Matt Jung, he and Jim Mayer still discussing timeline needs; no ETA but they expect shortly. I will follow up on Fri 4/25 for updates and req a decision by end of next week, at latest.
4/28 - Spoke with Matt Jung, he will have response by Thurs 5/1 on if they can perform an impact analysis and what the timing would be. I informed him this is SWIFT related and to a) notify Dip (CO) of issue and b) timing, we need to wrap up everything by 6/1.
5/5 - Spoke with Jim Mayer, he will est an observation of the canceled Qualys jobs and provide analysis write up. If ISCA observes jobs completed above the 90% KPI, we will nogtate an observation. If below the KPI, we will document an issue.
5/12 - Met on 5/9 w/ team. Expected analysis by 5/15. Will result in ISS for non-SWIFT schedules.
5/22 - Spoke w/ CO Delegate. Reviewed evidence, provided feedback. ETA by EOD 5/22. Test will result in an observation not an issue.
5/29 - Response received on 5/28. testing completion ETA 6/3.', 'Kushari, Dip (018642)', 'Jim Mayer', FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-03', '2025-02-28', '2025-05-30', '2025-05-30'),
    (18, 'VGCP-02173', 'Access requests for the Qualys application are processed by an authorized administrator upon receipt of a valid Sailpoint request', '3/30/25-OET back in Mikes review, observation discussed with Dave and Mike on 3/28 has been noted in DAT.
2/4/2025-Emailed Pavel and SMEs to schedule a walkthrough
2/7/25- Walktrhu scheduled for Tuesday 2/11
2/11/25-Walkthru rescheduled due to laptiop issues. Getting resolved today with TC
2/12/25-Walkthru completed, Evidence due date for 2/19
2/21/25-Evidence recieved
3/13/25-Potential Issue, will need a follow up meeting with Dave and Eric
3/27/25-DAT is complete, OET still in progress', 'Matskevich, Pavel (056961)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-11', '2025-02-28', '2025-03-28', '2025-03-30'),
    (19, 'VGCP-02971', 'Critical SWIFT File Integrity Monitoring Rules are recertified annually through a documented formal process', '2/4/2025-Emailed Pavel and SMEs to schedule a walkthrough
2/7/25- Walktrhu scheduled for Tuesday 2/11
2/11/25-Walkthru rescheduled due to laptiop issues. Getting resolved today with TC
2/13/25-Walkthru completed evidence due date for 2/20
2/25/25 JM - DAT approved, ready for next step and OET can begin.
2/26/25 JM - OET review completed, ready for BP.
3/5/25 JM - DAT approved in BP.
3/10/25-OET uploaded to BP
3/11/25 JM - OET approved in BP.', 'Matskevich, Pavel (056961)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-11', '2025-02-28', '2025-02-26', '2025-03-11'),
    (20, 'VGCP-03084', 'Vulnerabilities are rated for risk according to predefined criteria.', '2/4/2025-Emailed Pavel and SMEs to schedule a walkthrough
2/7/25- Walktrhu scheduled for Tuesday 2/11
2/11/25-Walkthru rescheduled due to laptiop issues. Getting resolved today with TC
2/12/25-Walkthru completed evidence due date for 2/19
2/28/25-DAT in Javiers review
3/3/2025-Working on OET
3/6/25-DAT uploaded to BP
3/6/25 JM - DAT approved in BP.
3/7/25 JM - OET reviewed with comment for action in cell N5 on the "SNOW Report-SWIFT" tab. once complete, OET ready for BP upload.
3/10/25-Adressed comment and uploaded OET to BP
3/11/25 JM - OET approved in BP.', 'Matskevich, Pavel (056961)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-04', '2025-02-28', '2025-03-07', '2025-03-11'),
    (21, 'VGCP-05700', 'Information from the vulnerability scanning tool is documented and reported.', '2/4/2025-Emailed Pavel and SMEs to schedule a walkthrough
2/7/25- Walktrhu scheduled for Tuesday 2/11
2/11/25-Walkthru rescheduled due to laptiop issues. Getting resolved today with TC
2/12/25-Walkthru completed evidence due date for 2/19
3/6/25-DAT in Javiers review
3/07/25 JM - DAT review complete, ready for BP upload.
3/10/25-DAT Uploaded into BP
3/11/25 JM - DAT approved in BP.
3/12/25 JM - OET review completed, ready for BP upload.
3/13/25-Test Uploaded in BP', 'Matskevich, Pavel (056961)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-02-11', '2025-02-28', '2025-03-11', '2025-03-12'),
    (23, 'VGCP-03131', 'UPDATE: Unique RSA Tokens or YubiKeys are assigned to individual users, and users are enrolled in Okta SSO, based on access management workflow, to support multi-factor authentication', 'MH - walkthru scheduled for 3/20
MH - walkthru rescheduled for 3/24 due to conflict of key participant
Control Owner: Alice Sherlock; Operational Advocate: Michelle Miller
4/2 - MB - Sent note to CO; will schedule walkthrough on 4/4 if no response.
4/7 - Sent questsion in advance as requested; no reponses as of 4/10
4/10 - scheduled walkthrough for 4/14
4/16 - RSA Hard/Soft token wlkthr cmpltd; sched Yubi wktht for 4/21
4/22 - RSA and Yubi designs out for review; ETA 4/29. RSA evidence out; ETA 5/6. No testing for Yubi.
5/6 - DAT completed. OET evidence received not reviewed, ETA 5/9 completion.', 'Sherlock, Alice (054225)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-02', '2025-03-31', '2025-05-15', '2025-05-12'),
    (24, 'VGCP-03621', 'A host reconciliation is conducted for the vulnerability scanning tool on a regular basis', 'DAT sent to CO for approval 3/19; Followed up on 3/25
OET evidence request sent 3/25/25
DAT and OET rec''d 3/28
DAT and OET Follow up questions sent on 4/1; spoke with Delegate, he plans on reviewing on 4/4.
4/10 - Still reviewing as of 4/4; need to circle back.
4/16 - Meeting w/ Matt Jung on 4/16 DAT and OET open requests.
4/21 - Evid req sent to Matt Jung on 4/16; awaiting evidence.
4/23 - Add''l walkthrough on 4/30 needed for script in order to test.
5/5 - Confirmed design Issue related to placement of supporting scritps in non-production region and changes w/o change records. Requested confirmation of facts and plan from Control Owner by 5/16.
5/12 Updated ETA to 5/30 given previous comment and date.
5/22 - DAT in L1 review (ISS confirmation); OET in BP approval.', 'Kushari, Dip (018642)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-10', '2025-03-31', '2025-05-30', '2025-06-03'),
    (25, 'VGCP-03625', 'Assets excluded from vulnerability scanning are reviewed and approved through a formal process', '3/27-DAT and OET uploaded in BP, waiting for John M to approve.
3/3-Walkthrough scheduled
3/12-Evidence Recieved
3/17-DAT ready for review
4/1- JM - DAT Approved in Ballast Point
4/1 - JM - OET Approved in Ballast Point', 'Matskevich, Pavel (056961)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-03', '2025-03-31', '2025-03-26', '2025-04-01'),
    (26, 'VGCP-03737', 'Assets excluded from vulnerability scanning are scanned semi-annually', '3/27-DAT and OET uploaded into BP, Waiting for John M to approve
3/17-DAT ready for review
3/3-Walkthrough scheduled
3/12-Evidence Recieved
3/17-DAT ready for review
4/1 - JM - DAT Approved in Ballast Point
4/1 - JM - OET Approved in Ballast Point', 'Matskevich, Pavel (056961)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-03', '2025-03-31', '2025-03-26', '2025-04-01'),
    (27, 'VGCP-03747', 'Vulnerabilities that cannot be remediated or remediated within SLA follow a formal exception process.', '4/10/2025 - JWM - OET approved in Archer
4/10/2025-OET uploaded in BP
4/9/2025 - JWM - DAT approved in BP
4/8/25-Addressed OET comments and back to John for review
4/7/25-DAT uploaded into BP ready for approval
4/2/2025- Followed up with Eric
3/30-Need a follow up with Eric S for OET, saw some deferred vulnerabilities for Aladdin assets but could not find the approvals necessary for them.
3/27-Addressed comments, DAT in Johns review
3/3-Walkthrough scheduled
3/12-Evidence Recieved
3/17-DAT ready for review', 'Matskevich, Pavel (056961)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-03', '2025-03-31', '2025-04-03', '2025-04-10'),
    (28, 'VGCP-03749', 'Failed authentication attempts from the vulnerability scanning tool are tracked and remediated', '3/31 CW: DAT approved in BP
OET evidence request 3/21/25
3/27 - Test evidence due diligence required. Follow up request sent to CO
3/31 - est meeting w/ delegate to review source file and recon file numbers.
4/3 - OET Questions; meeting on 4/14.
4/10 - Ready for testing; will still meet on 4/14
4/15 - Evidence request sent to Matt Jung.
4/21 - Test completed. Add''l evid needed for 5/14 Juniper devices below SLA
4/23 - OET in Review
4/28 CW: OET approved in BP', 'Kushari, Dip (018642)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-05', '2025-03-31', '2025-05-09', '2025-04-28'),
    (29, 'VGCP-05243', 'A Cyber Security Awareness Program is maintained by ES&F for National Cyber Security Awareness Month', '3/25 CW: BP team is working to fix BP issue. As of 3/25, still no solution. DAT and OET have both been reviewed and are ready for BP
BP issue preventing doc of DAT.
OET out for review.', 'Rushlow, Derric (016087)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-05', '2025-03-31', '2025-03-31', '2025-03-31'),
    (30, 'VGCP-05587', 'Security requirements for Vanguard applications are documented and maintained to protect against malicious attacks.', '3/21 CW: DAT reviewed and ready for BP
DAT and OET additional evidence re received on 3/19.
3/24 CW: DAT approved in BP', 'Danu, Florin (027636)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-03-10', '2025-03-31', '2025-03-31', '2025-03-26'),
    (31, 'VGCP-06563', 'Physical Security Officer resources, equipment and related systems are deployed as a layered construct, enterprise-wide.', '3/30/25-OET in John Review
3/26/25-DAT ready for BP
3/17-Evidence Recieved
3/12/24-Walktrhough completed
3/7-Walkthrough Scheduled
4/1 - JWM - DAT was approved in Ballast Point
4/1 - JWM - OET was approved in Ballast Point', 'Krieg, John (003930)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-06', '2025-03-31', '2025-03-31', '2025-04-01'),
    (32, 'VGCP-06769', 'A host reconciliation is conducted for the vulnerability scanning tool on a regular basis', 'DAT sent to CO for approval 3/19; Followed up on 3/25
OET evidence request sent 3/25/25
DAT and OET rec''d 3/28
DAT and OET Follow up questions sent on 4/1; spoke with Delegate, he plans on reviewing on 4/4.
4/10 - Still reviewing as of 4/4; need to circle back.
4/16 - Meeting w/ Matt Jung on 4/16 DAT and OET open requests.
4/21 - Evid req sent to Matt Jung on 4/16; awaiting evidence.
4/23 - Add''l walkthrough on 4/30 needed for script in order to test.
5/5 - Confirmed design Issue related to placement of supporting scritps in non-production region and changes w/o change records. Requested confirmation of facts and plan from Control Owner by 5/16.
5/12 Updated ETA to 5/30 given previous comment and date.
5/22 - OET completion expected 5/23', 'Kushari, Dip (018642)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-10', '2025-03-31', '2025-05-15', '2025-06-03'),
    (33, 'SWIFT #3', 'NEW CONTROL: SWIFT #3 Swift-specific Training (Phishing)', 'Recommended alginment with VGCP-05029. Awaiting Leadership disposition befor admin updates performed.', NULL, NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Addressing Comments', 'COMPLETED', '2025-03-06', '2025-03-31', '2025-03-31', '2025-03-14'),
    (34, 'VGCP-04305', 'Threat intelligence reports and follow-up reports are generated for security department heads and the CISO', 'Walkthrough scheduled 4/3
Issue satisfied - goes to Grant, Delp, and Jake.
4/10 - REQ2437497 sent for DAT review and OET documentation.; OBSERVATION
4/14 - Evidence review 4/24
4/24 - CO pushing till 5/6
5/9 - DAT and OET completed.', 'Mooney, Dennis (039771)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-10', '2025-04-30', '2025-05-15', '2025-05-15'),
    (35, 'VGCP-05553', 'The VSPL Information Security Policy Framework is reviewed and approved on an annual basis', '5/13: Ineffective control. ISS-19597 created and linked. No OET needed.
5/13/2025: JWM - DAT approved in Archer
5/12: DAT loaded to Archer for approval. Issue was created in Archer and linked to testing.
5/8: Paul said he''d review and have a reply by end of the week.
5/5: heard back from Neel. Waiting on final approval from Paul, but issue and action plan language has been provided.
4/30: Followed up with Paul for the review of the self-identified issues drafts.
4/14: Self-identified issue draft sent to Neel, Bernie, and Jake for feedback. Once received, issues will be created and linked in archer to the test
4/10/2025 - JWM - DAT ready for Archer
4/10: DAT ready for review again.
4/3/2025: DAT ready for review. Evidence for OET requested on 4/3/2025.
3/21: WT meeting with Neel scheduled for 3/31. Reached out to Neel regarding policy framework on Crewnet. Latest copy on CrewNet says Feb 2024. Reached out to Paul to confirm ownership', 'Lewis, Paul (037221)', NULL, FALSE, 'Clara', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, 'COMPLETED', '2025-03-31', '2025-04-30', NULL, '2025-05-13'),
    (36, 'VGCP-06294', 'Vanguard reviews annual information security attestations related to CPS 234 from Grow', '5/13: ISS-19596 linked
5/13/2025: JWM - OET Approved (Ineffective) in Archer
5/12: OET loaded to Archer for approval. Issue was created in Archer and linked to testing.
5/8: Paul said he''d review and have a reply by end of the week.
5/5: heard back from Neel. Waiting on final approval from Paul, but issue and action plan language has been provided.
4/30: Followed up with Paul for the review of the self-identified issues drafts.
4/22: Awaiting for AUS GRC team''s review of draft self-identified issue. They return from PTO on 4/29. Draft issue was submitted to them on 4/17.
4/16/2025 - JWM - DAT approved in Archer
4/14: DAT ready for approval in archer
4/14/2025: JWM DAT and OET ready for Archer
4/10: DAT and OET ready for review.
4/3: Follow-up meeting with Neel, Bernie, and John on 4/7 to discuss potential control failure or changes to control.
3/21: WT meeting with Neel scheduled for 3/31. Reached out to Paul to confirm ownership.', 'Lewis, Paul (037221)', NULL, FALSE, 'Clara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-31', '2025-04-30', NULL, '2025-05-13'),
    (37, 'VGCP-06320', 'VIA crew are required to take annual fraud training to understand how to identify and report suspected and actual fraud events', '4/28 - JWM - OET and DAT approved in Archer
4/16/2025 - JWM - DAT ready for Archer
4/14-DAT in John''s Review
4/10-Requested evidence and return date of 4/17
4/8-Follow up with Malcolm
4/2-Completed walktrhough with Malcolm, will need another meeting Monday or Tuesday, He was having some technical issues and we ran out of time to get through everything.
3/27/25-Reached out to Scott to schedule walkthrough with Malcolm Chau', 'Scott, Mason (064291)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-03-27', '2025-04-25', '2025-04-25', '2025-04-28'),
    (38, 'VGCP-06781', 'NEW CONTROL: Multi-channel client notifications - Following any Change of Details or cash redemption request, multi-channel notifications are sent to the registered mobile Ph, email and web-portal secure message account advising the client of the change/redemption', '5/2/2025 - JWM - DAT | OET Approved in Archer
5/1 - JWM - OET Worksheet reviewed
4/30/25-OET in Johns Review
4/30 - JWM - Reviewed updated DAT worksheet - Ready for Archer
4/27/25-Spoke to Malcolm about completion date for this control, waiting on evidence from IST team to start OET
4/23-Evidence request sent to Malcolm
4/14-Recieved word document of questions answered from Jason Tey IST run team
4/8-Follow up with Malcolm
4/2-Completed walktrhough with Malcolm, will need another meeting Monday or Tuesday, He was having some technical issues and we ran out of time to get through everything.
3/27/25-Reached out to Scott to schedule walkthrough with Malcolm Chau', 'Scott, Mason (064291)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing In Progress', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-03-27', '2025-04-25', '2025-05-02', '2025-05-02'),
    (39, 'VGCP-07289', 'Qualys Application IDs as related to the SWIFT environment have their passwords rotated annually.', '4/21 CW: OET approved in BP
4/10 CW: DAT approved in BP
Walkthrough scheduled 4/3
4/10 - DAT completed, OET evidence received.', 'Kushari, Dip (018642)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-07', '2025-04-30', '2025-04-30', '2025-04-21'),
    (40, 'VGCP-07290', 'TWS Application IDs as related to the SWIFT environment have their passwords rotated annually.', '4/21 CW: DATA and OET approved in BP
Walkthrough schedule 4/7
4/10 - DAT in L1 review; evidence to be sent out.
4/16 - OET in L1 review.', 'Olivos, Juan (041424)', NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-07', '2025-04-30', '2025-04-30', '2025-04-21'),
    (41, 'VGCP-07299', 'UPDATE: Threat Intelligence is ingested, analyzed, and triaged for handling based on priority and severity', 'Walkthrough scheduled 4/3
Recommend updates to the title and narrative; testing coverage 10/24 - 3/25 due to org and process changes; lastly CSOC does not provude evidence - are we ok with all?
4/10 - REQ2437497 sent for DAT review and OET documentation.
4/14 - Evidence review 4/24
4/24 - CO pushing till 5/6
5/12 - OET completed; DAT 5/13 meeting for Decision Tree evidence (can not be shared).', NULL, NULL, FALSE, 'Michel', 'COMPLETED', 'Testing In Progress', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-10', '2025-04-30', '2025-05-15', '2025-05-16'),
    (42, 'VGCP-07379', 'Vanguard reviews annual information security attestations related to CPS 234 from AIA', '5/13: ISS-19596 linked
5/13/2025: JWM - OET Approved (Ineffective) in Archer
5/12: OET loaded to Archer for approval. Issue was created in Archer and linked to testing.
5/8: Paul said he''d review and have a reply by end of the week.
5/5: heard back from Neel. Waiting on final approval from Paul, but issue and action plan language has been provided.
4/30: Followed up with Paul for the review of the self-identified issues drafts.
4/22: Awaiting for AUS GRC team''s review of draft self-identified issue. They return from PTO on 4/29. Draft issue was submitted to them on 4/17.
4/16/2025 - JWM - DAT approved in Archer
4/14?DAT ready for approval in archer
4/14/2025: JWM DAT and OET ready for Archer
4/10: DAT and OET ready for review
4/3: Testing for both DAT and OET is just about complete but awaiting outcome of 4/7 meeting in case changes need to be made.
3/21: WT meeting with Neel scheduled for 3/31. Reached out to Paul to confirm ownership.', 'Lewis, Paul (037221)', NULL, FALSE, 'Clara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-31', '2025-04-30', NULL, '2025-05-13'),
    (43, 'VGCP-07380', 'Vanguard reviews annual information security attestations related to CPS 234 from JP Morgan', '5/13: ISS-19596 linked
5/13/2025: JWM - OET Approved (Ineffective) in Archer
5/12: OET loaded to Archer for approval. Issue was created in Archer and linked to testing.
5/8: Paul said he''d review and have a reply by end of the week.
5/5: heard back from Neel. Waiting on final approval from Paul, but issue and action plan language has been provided.
4/30: Followed up with Paul for the review of the self-identified issues drafts.
4/22: Awaiting for AUS GRC team''s review of draft self-identified issue. They return from PTO on 4/29. Draft issue was submitted to them on 4/17.
4/16/2025 - JWM - DAT approved in Archer
4/14: DAT ready for approval in archer
4/14/2025: JWM DAT and OET ready for Archer
4/10: DAT and OET ready for review
4/3: Testing for both DAT and OET is just about complete but awaiting outcome of 4/7 meeting in case changes need to be made.
3/21: WT meeting with Neel scheduled for 3/31. Reached out to Paul to confirm ownership.', 'Lewis, Paul (037221)', NULL, FALSE, 'Clara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-03-31', '2025-04-30', NULL, '2025-05-13'),
    (44, 'VGCP-05976', 'An Asset Vulnerability Test (AVT) is conducted for the SWS-SwiftNet Application annually', '5/19/2025 - JWM - DAT and OET approved in Archer
5/15/25-DAT and OET uploaded in BP
5/13 - OET worksheet reviewed. Ready for Archer
5/8/25-OET in Johns Review, will upload both test after review of OET and potential comments are addressed
5/5/2025 - JWM - DAT Worksheet reviewed. Ready for Archer
4/30 Access to TSA module was granted yesterday to self provision evidence 4/24/2025-Walkthrough completed
4/21/2025-Walktrhough Sceduled for 4/24 4/10/2025-Emailed Bill and CC Tom Kercher and Evan Mitses to schedule walkthrough
Mark''s updates
5/14 CW: Re-assigned to Jason to complete testing.', 'Evenden, David (174378)', NULL, FALSE, 'Jason', 'COMPLETED', 'Walkthrough Completed', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-04-20', '2025-04-30', '2025-05-20', '2025-05-19'),
    (45, 'VGCP-05554', 'Ineffective information security controls are evaluated as potential material weaknesses and results are reported to the OST for notification as needed', '6/10 - DAT and OET approved in Archer
6/2: DAT and OET ready for approval in Archer
5/30: Received response back from Bernie. DAT and OET readyf or review
5/22: Bernie let me know that he was meeting with Neel and would have something back to me in the next few days. This is in response to my comments regarding the design. I have some evidence and will start documenting for the OET.
5/8: Bernie let me know he and Neel would be reviewing my questions for the narrative and have something back to me after their conversation.
5/2: Reviewed draft narrative and sent back to Neel and Bernie with questions/comments.
4/30: Received updated draft narrative from Neel and Bernie. I''ll review and send back to Neel and Bernie with comments and set up a follow-up meeting next week if needed.
4/25: Set up walkthrough meeting with Bernie and Neel on 4/29.', 'Kruger, Grant (100418)', NULL, FALSE, 'Clara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-25', '2025-05-31', NULL, '2025-06-10'),
    (46, 'VGCP-06381', 'VSPL Fraud Risk Assessment Profile Is reviewed and approved annually', '6/25-Updated control name as well as Narrative in Arher. Awaiting Johns Approval in Archer
6/20-Worksheet uploaded in Archer, ready for approval
6/18 - OET ready for Archer
6/12-OET worksheet created and in Johns review
6/10 - OET was ineffective. Missing worksheet attachment. Question whether to only attach issue doc
6/10 - DAT approved in Archer (JWM)
6/9/-OET failure ready for approval in BP, DAT ready for approval in BP
6/6-Issue and action plan open in Ballastpoint (ISS-19754&AP-35250)
5/29/- Mike and I addressed Victors Comments on Issue Narrative. Approved by Fraud team
5/29/-Sent issue Draft to Bob in ERM, waiting for feedback
5/29/Recieved feedback from Fraud team on Issue draft, will address their comments
5/29/DAT uploaded into BP
5/22-DAT is In review
5/22-Issue draft sent to Fraud Team for review
5/16/25-Meeting with Victor and Clara, this control will be a failure. Working on DAT and ISS
5/12- Meeting with Victor Kwong today
5/7/25-Walkthrough with Malcolm, will need a follow up.
5/5/25-Walkthrough with Malcolm scheduled for 5/6/25', 'Scott, Mason (064291)', 'Victor Kwong
Malcolm Chau', FALSE, 'Jason', 'COMPLETED', 'Walkthrough Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-02', '2025-05-31', '2025-05-31', '2025-06-26'),
    (47, 'VGCP-05029', 'Simulated phishing e-mails are sent to all crew for security awareness training.', '6/23/2025: OET approved in Archer
6/18/2025: OET waiting for approval in Archer
6/18/2025: OET ready for Archer
6/16: OET waiting for review
6/9: Making updates to OET and resubmitting
6/4: Additional evidence received and reviewed. OET drafted and submitted for review
6/3: Narrative approved, updated in Archer, DAT submitted
6/1: Draft of updated narrative sent to Derric; OET drafted; request for additional evidence sent (due 6/3)
5/30 CW: Jen needs to connect with Derric before entering into Archer
5/28: DAT ready for BP
5/22 DAT reviewed, comments added. Comments addressed and waiting to input to BP
5/16 Evidence request email sent. Evidence due 5/27
5/16 Additional meeting to review evidencing needs and SWIFT testing frequency. DAT submitted for review
5/15 Additional meeting moved to 5/16
5/12 Additional walkthrough scheduled for 5/15 to veryify reporting needs and a few narrative changes
5/7 Walkthrough conducted; additional meeting needed to review evidencing
4/29 Introductory email sent; walkthrough scheduled 5/7', 'Rushlow, Derric (016087)', NULL, FALSE, 'Jen', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-29', '2025-05-31', '2025-06-04', '2025-06-23'),
    (48, 'VGCP-03129', 'Out-of-sync ID Vault passwords for Individual privileged accounts are reconciled with source systems to support continued CyberArk use for MFA and password rotation.', '7/10 - DAT in Archer, completed; OET in review. OET was awaiting BU documentation on Issue.
7/7 CW: DAT reviewed and ready for Archer
6/30 - DAT to be updated on 7/1; OET completed, awaiting BU ISS notification.
6/24 - meeting on 6/30 to discuss OET sample observation; ie 1 out of 3 months sampled report not performed. Requested and received additional 3 months sampling. Testing to be performed 6/26. DAT, received confirmation on open question and will update 6/26.
6/3 - meeting at 130 on 6/3 to discuss OET evidence and DAT needs.
5/5 - Walkthrough completed by prior ISCA Assoc. Requires review against new design standard to determine if add''l walktrhough required.
5/15 - 2nd walkthrough scheduled 5/15
5/22 - DAT out for CO review; OET evidence requsted and received.
5/29 OET evidence received 5/23, meeting est 5/29 to review report. DAT evidence received however awaiting CO response to question.
Mark''s updates
5/14 CW: Redistributed to Mike to complete testing
1/24 reached out to control owner to schedule walkthru
1/29 Walkthru scheduled for 2/7
2/11 evidence request sent due 2/18. updated eta.
2/11 sent follow-up questions for Ryan S.
2/19 received response. Setup another walk thru for Red State procedure for 2/20
2/26 setup Red state walkthru for 2/27
3/18 followup meeting set for 3/20 for additional questions', 'Sepe, Ryan (181019)', 'Samantha Wittig; Richard Franck', FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-02', '2025-05-31', '2025-05-31', '2025-07-08'),
    (49, 'VGCP-05382', 'SWIFT LSO and RSO accounts are each protected in CyberArk and have separate safes and AD groups to ensure separation of duties.', '7/1/2025: DAT approved in Archer (JWM)
6/30/2025: DAT ready for Archer (JWM)
6/30 - DAT was documented as is. CO has not responded to multiple requests for review.
6/26/2025: OET approved in Archer (JWM); DAT still pending, so not closed
6/24: DAT still awaitomg final approval from Owner. Decision to document as is.
6/17 - OET ready for Archer (JWM)
6/3 : DAT review on 130 meeting 6/3
5/5 - Walkthrough completed by prior ISCA Assoc. Requires review against new design standard to determine if add''l walktrhough required.
5/15 - 2nd walkthrough scheduled 5/15
5/19 - Meeting extended to 5/20
5/22 - DAT out for CO review; OET evidence requsted.
5/29 OET completed out for L1 review. DAT CO expected EOD 5/29; completion ETA 5/30.
Mark''s updates
5/14 CW: Redistributed to Mike to complete testing
1/24 reached out to control owner to schedule walkthru
1/29 Walkthru scheduled for 2/7
2/11 evidence request sent due 2/18. updated eta.
2/13 reached out to CSOC with a question.
2/18 sent follow-up question to CSOC
2/19 DAT in review
2/19 CW: DAT reviewed with comments
2/20 addressing comments.
3/18 followup meeting set for 3/20 for additional questions', 'Sepe, Ryan (181019)', '-', FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-02', '2025-05-31', '2025-05-31', '2025-06-30'),
    (50, 'Swift #4', 'SSH Keys', '4/28 - Wlkthr schld for 5/2
5/5 - Require meeting w/ ISCA Lead. Potential duplication with existing controls.
5/7 - Spoke w/ Clara for agreement; Babu (SWIFT Tech Assoc) and I spoke and SSH keys covered under existing contros (VGCP-02973 and VGCP-04210). Clara and I reviewed refernced controls and confirmed. ISCA should review for SSH Key deployement to ID Vault for this control and KMS Keys due to transition to Cloud.', NULL, NULL, FALSE, 'Michel', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-04-25', '2025-05-31', '2025-05-31', '2025-05-07'),
    (51, 'VGCP-02942', 'Individual OS privileged account users must use two-factor authentication to obtain their secure OS password, which is stored and rotated in ID Vault.', '5/27: OET loaded to BP for approval
5/22: OET ready for load into BP
5/21: Submitted OET to Clara for review
5/21: Loaded DAT into Archer
5/15: DAT sent to Clara for review
5/9: DAT sent to Clara for review with new narrative
5/5: Conducted walkthrough with Ryan Sepe, narrative is incorrect and in progress of re-writing
4/29: Set up walkthrough meeting with Michelle and Ryan on 5/5
Mark''s updates
5/14 CW: Re-assigned to Sara to complete testing.
MH - walkthru scheduled for 3/24', 'Miller, Michelle (102637)', NULL, FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-05', '2025-05-31', '2025-05-31', '2025-05-28'),
    (52, 'VGCP-03130', 'Monthly quality control checks are performed between SWIFT privileged accounts and ID Vault to ensure all privileged accounts are in ID Vault. Discrepancies are researched and remediated by the ID Vault Team.', '5/29: OET comments addressed and sent back for review
5/28 CW: OET reviewed with comments
5/27: Sent OET to Clara for review
5/21: OET in progress awaiting evidence from Michelle
5/20: DAT loaded into BP for approval.
5/19: Sent DAT to Clara for review
5/15: Send DAT to Clara for review
5/14: Follow up mtg with Michelle for clarifying answers to some DAT questions
5/6: Send DAT to Clara for review
5/5: Conducted walkthrough with Michelle Miller. Indicated that this was previously done. Narrative is accurate and she will send over email with evidence sent to Mark previously.
4/29: Set up walkthrough meeting with Michelle and Ryan on 5/5
Mark''s updates
5/14 CW: Re-assigned to Sara to complete testing.
MH - walk thru scheduled for 3/20
MH - walkthru rescheduled for 3/21 due to conflict of key participant
MH - walkthru complete. testing in progress.
MH DAT in review', 'Miller, Michelle (102637)', NULL, FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-05', '2025-05-31', '2025-05-31', '2025-05-30'),
    (53, 'VGCP-04210', 'Shared account session usage conducted on SWIFT servers are protected by a cryptographic protocol.', '5/27: OET loaded to BP for approval
5/14: Sent reviewed comments OET to Clara
5/13 CW: DAT approved in BP; OET reviewed with comments
5/9: OET to Clara for review
5/8: Started OET evidence gathering and compiling into file
5/8: DAT approval
5/7: Send DAT to Clara for review
5/7: Conducted walkthrough with Michelle Miller and Ryan Sepe. Changes needed to control title, otherwise narrative accurate.
4/29: Set up walkthrough meeting with Michelle and Ryan on 5/7
Mark''s updates
5/14 CW: Re-assigned to Sara to complete testing.
MH walkthru scheduled for 3/25', 'Sepe, Ryan (181019)', NULL, FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-07', '2025-05-31', '2025-05-31', '2025-05-28'),
    (54, 'VGCP-06309', 'NEW CONTROL: Fraud operations resourcing conducted by appropriately skilled and experienced personnel, independent of operational business units', '6/10/2025 - DAT and OET approved in Archer
6/9/25-DAT and OET test ready for approval in Archer
6/2/2025 - JWM - DAT worksheet reviewed and ready for Archer
5/29/25-DAT in review, OET in progress
5/15/25-Will start working on DAT, need more time to complete
Walkthrough scheduled for 5/14', 'Scott, Mason (064291)', NULL, FALSE, 'Jason', 'COMPLETED', 'Walkthrough Completed', 'COMPLETED', NULL, 'COMPLETED', '2025-05-09', '2025-05-31', '2025-06-06', '2025-06-10'),
    (55, 'VGCP-06361', 'Annual Review of the Fraud Risk Management Policy Framework', '6/18 - DAT was approved in Archer
6/11-Uploaded DAT to BP and linked exisitng issue and AP to test
6/10 - Revised DAT worksheet with exception was reviewed. Ready for Archer
6/9-Drafted up Issue narrative, Sent to Fraud team and ERM, giving them till Tuesday for feedback
6/6-DAT sent back to John for review with excpetion noted in narrative
5/29-Met with Malcolm and Bernie. This will be a finding. Working on Issue draft Narrative
5/23-Potential Issue, board has not reviewed and approved policy as of right now, Policy was approved in March last year, missing the annual cadence. Board is scheduled to review it next week.
5/19/2025 - JWM - DAT ready for Archer
Walkthrough scheduled for 5/14', 'Scott, Mason (064291)', NULL, FALSE, 'Jason', 'COMPLETED', 'Walkthrough Completed', 'COMPLETED', NULL, 'COMPLETED', '2025-05-09', '2025-05-31', '2025-05-30', '2025-06-18'),
    (56, 'VGCP-06782', 'Fraud awareness material and reporting mechanisms are published on Vanguards public website to enable members to identify and report incidences of suspected fraud.', '6/10/2025 - OET approved in Archer
6/9/25-OET is awaiting approval in Archer
5/29/2025-OET uploaded into Archer
5/28/2025 - JWM - OET ready for Archer
5/28/2025 - JWM - DAT approved in Archer
5/23/25-DAT uplaoded to Archer
5/19/2025 - JWM - DAT ready for Archer
Walkthrough scheduled for 5/14', 'Scott, Mason (064291)', NULL, FALSE, 'Jason', 'COMPLETED', 'Walkthrough Completed', 'COMPLETED', NULL, 'COMPLETED', '2025-05-09', '2025-05-31', '2025-05-28', '2025-06-10'),
    (58, 'VGCP-06121', 'Critical SWIFT File Integrity Monitoring rules are created through a formal process', '8/18: Uploaded DAT and OET to Archer.
8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11: Upload DAT to Archer.
8/8 OET ready for Archer. Waiting to get access to Archer to upload DAT and OET.
8/7: DAT ready for Archer. Michael Hatch waiting for access to Archer (unable to sign in to Archer today; called tech support for assistance). OET is in review.
8/6: Submited DAT and OET for review.
8/5: Recieved comments on the DAT and will update by EOD 8/5. Plan to complete OET by EOD 8/5.
8/1: DAT completed and submitted for review by 12 pm ET 8/1.
7/31: Reviewed DAT with DT SME (Jos) and need to make updates based on feedback from Jos. Estimated DAT to be put into review on 8/1.
7/30 Asked for SharePoint access from SMEs to get additional information, waiting to get approval
7/29 Worked on structure of the OET evidence
7/28 Reviewed Claras comments for DAT and updating DAT to make sure all comments were addressed regarding 4 pillars
7/18 DAT in review
7/14 OET evidence gathered
7/7 OET in progress and gathered evidence
7/2 DAT evidence gathered
6/30 DAT in progress and gathered evidence
6/26 Sanni Kommoju said he can have evidence delivered to me on 6/30
6/16 Spoke on via teams to set up the walkthrough for VGCP-06121 for 6/17.
Still waiting for the evidence for this control and reminded him on 6/23.
Reached out to him 3 - 4 times.
6/10 Sanni Kommoju reached back out to me on via email to include Matthew McFetridge on Walkthroughs.
6/18 evidence request
6/17 Walkthrough scheduled
6/4 reached out to SMEs to schedule walkthrough

', 'Matskevich, Pavel (056961)', 'Sanni Kommoju
Matthew McFetridge', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-04', '2025-06-30', '2025-08-15', '2025-08-18'),
    (59, 'VGCP-08069', 'NEW CONTROL: Information from the cloud vulnerability scanning tool is documented and reported.', '8/18: Uploaded DAT and OET to Archer.
8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11/2025: OET Ready for Archer
8/11: Upload DAT to Archer.
8/8: DAT ready for Archer, OET in review.
8/6: Submited DAT and OET for review.
8/5: Recieved feedback on DAT and estamited to update DAT and complete OET by EOD 8/6.
8/1: Completing DAT and submitting for review by EOD 8/1.
7/31: Reviewed DAT with DT SME (Jos) and need to make updates based on feedback from Jos. Estimated DAT to be put into review on 8/1.
7/30 Reached out to SME for additional evidence. Will review with Deloitte SME (Jos) today for additional support.
7/28 Reviewed Claras comments, updating the DAT design of the control, for the process of the data being documented from WIZ to Tableau, along with the 4 pillars. Potential may need additional evidence from SME Eric Suchecki. Will be escalated to Deloitte SME (Jos) for additional questions.
7/23 DAT in review
7/11 I have to fully redact all evidence for DAT
7/11 DAT in progress and gathering evidence
7/10 2nd Walkthrough
6/27 Meeting with Eric Suchecki to understand the control.
6/26 Sanni Kommoju looked at the control said Eric Suchecki or VM Team is responsible for this control.
6/18 SME got changed to Sanni Kommoju, I reached out to Sanni to confirm this information. I am still waiting to see if this information is accurate.
6/18 I was informed by Eric Suchecki that Sanni Kommoju would do taking control VGCP-08069.
6/25 Walkthrough rescheduled. Schedule conflict with Sanni Kommoju.
6/9 reached out to the SMEs to schedule walkthrough
', 'Matskevich, Pavel (056961)', 'Sanni Kommoju
Matthew McFetridge
Or
Eric Suchecki
Aditya Shah', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-09', '2025-06-30', '2025-08-15', '2025-08-18'),
    (60, 'VGCP-08138', 'SWIFT: Cloud vulnerability Issues are rated for risk according to predefined criteria.', '8/18: Uploaded DAT and OET to Archer.
8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11/2025: OET Ready for Archer
8/11: Upload OET and DAT to Archer.
8/8 OET ready for Archer. Waiting to get access to Archer to upload DAT and OET.
8/7: DAT ready for Archer. Michael Hatch waiting for access to Archer (unable to sign in to Archer today; called tech support for assistance). OET is in review.
8/6: Plan to submit OET by EOD 8/6.
8/5: Plan to upload DAT to Archer and complete OET by EOD 8/5.
8/1: Waiting for feedback on DAT.
7/31: Reviewed DAT with DT SME (Jos) and submitted for review.
7/30: Completed DAT and will review with DT SME (Jos) today to get additional feedback if applicable.
7/29: Michael Hatch reviewed Clara''s comments, control walkthrough video / notes and began updating DAT. Improved ''Design Understanding'' section by logically outlinting the process and providing screesnhots for reference of material content. Potentially need to request additional evidence from control SME (Eric Suchecki) depending on feedback from Deloitte SME (Jos).
7/23 DAT in review
7/17 New evidence for OET 2nd walkthrough
7/7 I have to fully redact all evidence for OET
7/7 OET in progress and gathering evidence
7/7 I have to fully redact all evidence for DAT
6/30 DAT in progress and gathering evidence
6/27 Walkthrough rescheduled
6/23 He reached back out to me on to schedule time for a proper walkthrough.
6/18 Eric Suchecki meet with me on to discuss the controls VGCP-08069, VGCP-08138, VGCP-08139, & VGCP-08140 after no one responded to my email on 6/9. He took the time to explain to me that Aditya and himself would be doing VGCP-08138 & VGCP-08139, He gave me the links to their system but still need to set up time for a walkthrough.
Reached out to him 3 times.
6/9 reached out to SMEs to schedule walkthrough.', 'Matskevich, Pavel (056961)', 'Eric Suchecki
Aditya Shah', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-09', '2025-06-30', '2025-08-15', '2025-08-18'),
    (61, 'VGCP-08139', 'SWIFT: Cloud vulnerability Findings are rated for risk according to predefined criteria.', '8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11/2025: OET Ready for Archer
8/11: Upload DAT to Archer.
8/8: DAT ready for Archer, OET in review.
8/7: DAT ready for Archer. Michael Hatch waiting for access to Archer (unable to sign in to Archer today; called tech support for assistance). OET is in review.
8/6: Plan to submit OET by EOD 8/6.
8/5: Plan to upload DAT to Archer and complete OET by EOD 8/5.
8/1: Waiting for feedback on DAT.
7/31: Reviewed DAT with DT SME (Jos) and submitted for review.
7/30: Completed DAT and will review with DT SME (Jos) today to get additional feedback if applicable.
7/29: Michael Hatch to begin reviewing Clara''s comments, control walkthrough video / notes and begin updating DAT today (7/29/25). Any questions will be escalated to Deloitte SME (Jos).
7/23 DAT in review
7/17 New evidence for OET 2nd walkthrough
7/7 I have to fully redact all evidence for OET
7/7 OET in progress and gathering evidence
7/7 I have to fully redact all evidence for DAT
6/30 DAT in progress and gathering evidence
6/27 Walkthrough rescheduled
6/23 He reached back out to me on to schedule time for a proper walkthrough.
6/18 Eric Suchecki meet with me on to discuss the controls VGCP-08069, VGCP-08138, VGCP-08139, & VGCP-08140 after no one responded to my email on 6/9. He took the time to explain to me that Aditya and himself would be doing VGCP-08138 & VGCP-08139, He gave me the links to their system but still need to set up time for a walkthrough.
Reached out to him 3 times.
6/9 reached out to SMEs to schedule walkthrough.', 'Matskevich, Pavel (056961)', 'Eric Suchecki
Aditya Shah', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-09', '2025-06-30', '2025-08-15', '2025-08-18'),
    (62, 'VGCP-08140', 'SWIFT: Cloud vulnerabilities that cannot be remediated or remediated within SLA follow a formal exception process', '8/18: Uploaded DAT and OET to Archer.
8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11/2025: OET Ready for Archer
8/11: Upload DAT to Archer.
8/8: DAT ready for Archer, OET in review.
8/7: DAT ready for Archer. Michael Hatch waiting for access to Archer (unable to sign in to Archer today; called tech support for assistance). OET is in review.
8/6: Plan to submit OET by EOD 8/6.
8/5: Plan to upload DAT to Archer and complete OET by EOD 8/5.
8/1: Waiting for feedback on DAT.
7/31: Reviewed DAT with DT SME (Jos) and submitted for review.
7/30: Beging reviewing control walkthrough video / notes and beging updating DAT.
7/29: Michael Hatch to begin reviewing Clara''s comments, control walkthrough video / notes and begin updating DAT today (7/29/25) or tomorrow (7/30/25) depending on timing of completion of review and uplift of VGCP-08138 and VGCP-08139. Any questions will be escalated to Deloitte SME (Jos).
7/23 DAT in review
7/17 New evidence for OET 2nd walkthrough
7/7 I have to fully redact all evidence for OET
7/7 OET in progress and gathering evidence
7/7 I have to fully redact all evidence for DAT
6/30 DAT in progress and gathering evidence
6/18, I reached out to him specifically about that control & he said he had availability.
Walkthrough scheduled for 6/26.
Reached out to Aaron Burgess 3 times, Aaron Burgess was not receptive to any of my communications efforts whether it be email or teams until Eric Suchecki specified on a walkthrough that Aaron Burgess would be dealing with VGCP-08140.
6/9 reached out to SMEs to schedule walkthrough', 'Matskevich, Pavel (056961)', 'Aaron Burgess
Eric Suchecki', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-09', '2025-06-30', '2025-08-15', '2025-08-18'),
    (63, 'VGCP-08293', 'Critical File Integrity Monitoring rules for cloud SWIFT applications are created through a formal process', '8/18: Uploaded DAT and OET to Archer.
8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11/2025: OET Ready for Archer
8/11: Upload DAT to Archer.
8/8: DAT ready for Archer, OET in review.
8/7: DAT ready for Archer. Michael Hatch waiting for access to Archer (unable to sign in to Archer today; called tech support for assistance). OET is in review.
8/6: Submited DAT and OET for review.
8/5: Recieved feedback on DAT and plan to update and complete OET by EOD 8/6.
8/4: Requesting one more piece of information for DAT to be complete (JWM)
8/1: Completing DAT and submitting for review by EOD 8/1.
7/31: Reviewed DAT with DT SME (Jos) and need to make updates based on feedback from Jos. Estimated DAT to be put into review on 8/1.
7/30 Asked for SharePoint access from SMEs to get additional information, waiting to get approval
7/30: Reviewing control walkthrough video / notes and started updating DAT.
7/29: Michael Hatch to begin reviewing Clara''s comments, control walkthrough video / notes and begin updating DAT tomorrow (7/30/25) depending on timing of completion of review and uplift of VGCP-08138, VGCP-08139, and VGCP-08140. Any questions will be escalated to Deloitte SME (Jos).
7/18 DAT in review
7/16 OET evidence gathered
7/9 OET in progress and gathering evidence
7/7 DAT evidence gathered
6/30 DAT in progress and gathering evidence
6/30 Walkthrough scheduled
6/10 Sanni reached back out to me on via email to include Matthew McFetridge on Walkthroughs.
Reached out to him about his other 2 controls VGCP-08293 & VGCP-08294 after the meeting on 6/17, no respond until 6/24, saying his calendar is now up to date.
Reached out to him 3 - 4 times.
6/4 reached out to SMEs to schedule walkthrough
', 'Matskevich, Pavel (056961)', 'Sanni Kommoju
Matthew McFetridge', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-04', '2025-06-30', '2025-08-15', '2025-08-18'),
    (64, 'VGCP-08294', 'Critical File Integrity Monitoring rules for cloud SWIFT applications are recertified annually through a documented formal process', '7/9 Gathered evidence and rules have been deployed to the cloud
7/2 This recertification control cant be tested until next year, can close out this control out
6/30 DAT in progress and gathering evidence
6/30 Walkthrough scheduled
6/10 Sanni reached back out to me on via email to include Matthew McFetridge on Walkthroughs.
Reached out to him about his other 2 controls VGCP-08293 & VGCP-08294 after the meeting on 6/17, no respond until 6/24, saying his calendar is now up to date.
Reached out to him 3 - 4 times.
6/4 reached out to SMEs to schedule walkthrough', 'Matskevich, Pavel (056961)', 'Sanni Kommoju
Matthew McFetridge', FALSE, 'Jahad', 'IN_PROGRESS', 'Addressing Comments', 'COMPLETED', NULL, 'IN_PROGRESS', '2025-06-04', '2025-06-30', '2025-08-15', NULL),
    (65, 'VGCP-08430', 'NEW CONTROL: Scans are monitored and acted upon if running >72 hours (SAEP)', '8/18: Uploaded DAT and OET to Archer.
8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11/2025: OET Ready for Archer
8/11: Upload DAT to Archer.
8/8: DAT ready for Archer, OET in review.
8/6: Submited OET for review.
8/5: Updated feedback on DAT and completed and submitted OET for review on 8/5.
8/1: DAT completed and submitted for review by 12 pm ET 8/1.
7/31: Reviewed DAT with DT SME (Jos) and need to make updates based on feedback from Jos. Estimated DAT to be put into review on 8/1.
7/30 Asked for Wiz access from SMEs to get additional information, waiting to get approval
7/29 Worked on structure of the OET evidence
7/28 Reviewed Claras comments for DAT and updated DAT for Design of the control, evaluation period, 4 pillars, how it is configured, 72 hours & monitoring consists of.
7/22 DAT in review
7/18 OET evidence gathered
7/11 OET in progress and gathered evidence
7/11 DAT evidence gathered
7/7 DAT in progress and waiting for the evidence
6/30 DAT in progress and gathering evidence
6/26 Walkthrough scheduled.
6/12 I pinned Subha Dasgupta on teams, Subha then responded to me and responded back to my email. Subha Dasgupta said her only available would be 6/26 for 30 mins.
I said I do think that I can work for 2 new controls in an half hour call.
She did not respond, and I let the team know.
Reached out to Subha 3 times.
6/9 reached out to SMEs to schedule walkthrough

', 'Sadik, Michael (018421)', 'Subha Dasgupta
Mahi Kandru', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-09', '2025-06-30', '2025-08-15', '2025-08-18'),
    (66, 'VGCP-08432', 'NEW CONTROL: The Wiz System Health dashboard monitors system health for Swift (SAEP)', '8/18: Uploaded DAT and OET to Archer.
8/14: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/13: Upload DAT and OET to Archer once exception form is filled out by Vivek as MH does not have permission to upload documents to Archer.
8/12: Upload DAT and OET to Archer once exception form is filled out and MH has permission to upload documents to Archer.
8/11/2025: OET Ready for Archer
8/11: Upload DAT to Archer.
8/8: DAT ready for Archer, OET in review.
8/7: DAT ready for Archer. Michael Hatch waiting for access to Archer (unable to sign in to Archer today; called tech support for assistance). OET is in review.
8/6: Submited OET for review. DAT ready to submit to Archer
8/5: Updated feedback on DAT and completed and submitted OET for review on 8/5.
8/1: DAT completed and submitted for review by 12 pm ET 8/1.
7/31: Reviewed DAT with DT SME (Jos) and need to make updates based on feedback from Jos. Estimated DAT to be put into review on 8/1.
7/30 Asked for Wiz access from SMEs to get additional information, waiting to get approval
7/29 Worked on structure of the OET evidence
7/28 Reviewed Claras comments for DAT and updated DAT for Design of the control, evaluation period, 4 pillars, & how it is ran daily.
7/22 DAT in review
7/18 OET evidence gathered
7/11 OET in progress and gathered evidence
7/11 DAT evidence gathered
7/7 DAT in progress and waiting for the evidence
6/30 DAT in progress and gathering evidence
6/26 Walkthrough scheduled.
6/12 I pinned Subha Dasgupta on teams, Subha then responded to me and responded back to my email. Subha Dasgupta said her only available would be 6/26 for 30 mins.
I said I do think that I can work for 2 new controls in an half hour call.
She did not respond, and I let the team know.
Reached out to Subha 3 times.
6/9 reached out to SMEs to schedule walkthrough

', 'Sadik, Michael (018421)', 'Subha Dasgupta
Mahi Kandru', FALSE, 'Jahad', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-09', '2025-06-30', '2025-08-15', '2025-08-18'),
    (67, 'VGCP-05802', 'Multifactor Authentication is enforced for logging into Australian Vanguard portal', '7/7 OET in progress and waiting for the evidence', 'Scott, Mason (064291)', 'Malcolm Chau
Simon Millar
Smit Patel', FALSE, 'Jason', 'COMPLETED', 'Testing In Progress', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-06-11', '2025-06-30', '2025-07-04', '2025-06-30'),
    (68, 'VGCP-05803', 'An electronic Identity Verification (IDV) check is conducted as part of the Know Your Customer (KYC)/Anti-Money laundering (AML) onboarding of Direct Investor accounts and for Superannuation account consolidation.', '6/30 DAT in progress and gathering evidence', 'Scott, Mason (064291)', 'Malcolm Chau
Jeremy Bond', FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, 'COMPLETED', '2025-06-11', '2025-06-30', NULL, '2025-06-30'),
    (69, 'VGCP-06780', 'OKTA automatic account lookout is enforced for both invalid Multifactor Authentication (MFA) attempts and password attempts.', '6/26 Walkthrough scheduled.', 'Scott, Mason (064291)', 'Malcolm Chau
Simon Millar
Smit Patel', FALSE, 'Jason', 'COMPLETED', 'Testing In Progress', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-06-11', '2025-06-30', '2025-07-03', '2025-06-30'),
    (70, 'VGCP-05026', 'Every 2 years a table-top exercise (TTX) is conducted of a scenario-based security event within the SWIFT network and action items are documented to address uncovered gaps.', '6/12 I pinned Subha Dasgupta on teams, Subha then responded to me and responded back to my email. Subha Dasgupta said her only available would be 6/26 for 30 mins.', 'Schellhammer, Robert (018822)', NULL, FALSE, 'Jen', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-01', '2025-06-30', NULL, '2025-06-11'),
    (71, 'VGCP-06562', 'Enterprise Security & Fraud generates role descriptions in compliance with established HR processes.', 'I said I do think that I can work for 2 new controls in an half hour call.', 'Flannery, Cheryl (172676)', 'Owner', FALSE, 'Jen', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-01', '2025-06-30', NULL, '2025-06-27'),
    (72, 'VGCP-07997', 'NDA and SLAs are documented and established within the service agreement between Vanguard and BlackRock', NULL, 'Malley, John (012569)', 'Owner', FALSE, 'Jen', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-01', '2025-06-30', NULL, '2025-07-10'),
    (73, 'VGCP-07998', 'The annual risk acceptance of BlackRocks usage of Vanguards BIC is conducted', 'Reached out to Subha 3 times.', 'Malley, John (012569)', 'Owner', FALSE, 'Jen', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-01', '2025-06-30', NULL, '2025-06-26'),
    (74, 'VGCP-03054', 'Antimalware software protections are optimally configured', '6/9 reached out to SMEs to schedule walkthrough', 'Buera, Edward (031900)', 'Owner', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-30', '2025-06-30', '2025-06-30', '2025-06-25'),
    (75, 'VGCP-03352', 'Firewall Rule Requests are reviewed and approved', '6/26: OET submitted to Clara for review
6/24- DAT ready for approval in Archer
6/18/2025: DAT ready for Archer (JWM)
6/16: DAT submitted for review
6/12: walkthrough meeting completed
6/5: Email requesting evidence and walkthrough mtg scheduled- 6/12
5/30: SNOW ticket opened for mtg request', 'Schellhammer, Robert (018822)', 'Owner', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-30', '2025-06-30', '2025-06-30', '2025-06-30'),
    (76, 'VGCP-05221', 'An end-to-end comprehensive firewall rule review is conducted on an annual basis for SWIFT secure zone perimeter firewalls.', '6/24: OET sent to Clara, ready for review
6/24 - DAT ready for approval in Archer
6/18/2025: DAT ready for Archer (JWM)
6/16: DAT submitted for review
6/12: walkthrough meeting completed
6/5: Email requesting evidence and walkthrough mtg scheduled - 6/12
5/30: SNOW ticket opened for mtg request', 'Schellhammer, Robert (018822)', 'Owner', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-05-30', '2025-06-30', '2025-06-30', '2025-06-25'),
    (77, 'VGCP-05593', 'The Information Security Incident Response Team (ISIRT) Plan is reviewed and approved at least annually for security incident handling', '6/24: email for evidence sent to Dan Reilly - rec''v one piece, waiting for final piece
6/24- DAT ready for approval in Archer
6/18/2025: DAT ready for Archer (JWM)
6/16: DAT submitted for review
6/12: walkthrough meeting completed
6/5: Email requesting evidence and walkthrough mtg scheduled - 6/12
5/30: SNOW ticket opened for mtg request', 'Schellhammer, Robert (018822)', 'Owner', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-05-30', '2025-06-30', '2025-06-30', '2025-06-27'),
    (78, 'VGCP-05697', 'New hires are assigned security training within 60 days.', '6/13 held initiial meeting with Derric R. Acheduled walk thru for 6/19 due to Sri V being OOO until 6/17
6/18 Walkthru held
6/24 DAT in review
6/26 OET in progress received evidence
6/30 DAT back in progress with focus on Annual updates to New Hire Security training. reached out to Derric R and Sri V with questions and to determine if they would prefer to meet.
7/2 received answers working on DAT. Have one question still out.
7/2 DAT in review
7/7 CW: DAT reviewed with minor comments
7/8 DAT updated and back in review
7/8 DAT uploaded to Archer for Clara approval
7/8 requested and received additonal evidence. Working on OET.
7/9 working with Sri to understand the evidence received.
7/9 Sri clarified. waiting on one peice of evidence from Derric R.
7/11 reached out to Derric, still trying to find evidence needed.
7/12 Derric on PTO. Sri trying to help out with missing evidence.
7/16 sent follow-up to Sri to see if he found anything while Derric is out
7/16 received evidence from Sri. It is not sufficient. Waiting for Derric to return.
7/31 revewing evidence Sri send before reaching out to Derric again
8/18: Control assigned to Michael Hatch; discuss with Clara the current status of the conrol
8/19: Based on review of OET, sufficient evidence was collected. Have suggestions to update OET; waiting to meet with Clara before making updates.
8/21: Update OET and submit for review by EOD today.
8/22: OET completed and in review.
8/25: DAT and OET in BP and ready for review', 'Rushlow, Derric (016087)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-06-11', '2025-08-29', '2025-08-29', '2025-08-25'),
    (79, 'VGCP-05931', 'Targeted role groups get consistent and needed training.', '7/30 CW: This control has been retired
6/13 held initiial meeting with Derric R. Acheduled walk thru for 6/19 due to Sri V being OOO until 6/17
6/18 Walkthru held
6/24 following walk thru followed up with Clara. The SALT does not do role specific training therefore there is not control and nothing to test. Clara to follow-up to retire.
6/30 met with John M and Clara. discussed retiring this control noting that this control is part of modernization. Sent email to Cherly requesting her final approval to retire.
7/16 John will discuss with Cheryl in 1x1
7/30 per Cheryl this can be retired. reached out to Clara to find out how to retire this.', 'Rushlow, Derric (016087)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, 'COMPLETED', '2025-06-11', '2025-06-30', '2025-07-15', NULL),
    (80, 'VGCP-03002', 'An Identity and Access Management Policy applies security principles of need-to-know, least privilege, and separation of duties.', '7/30/2025 - OET approved in Archer
7/29/2025-OET uploaded into Archer
7/25/2025-DAT approved in Archer
7/22/2025 - DAT worksheet reviewed. Ready for Archer
7/22/25-Will have OET in review when I return on 7/23
7/18/2025-DAT in review
7/16/25-Walkthrough completed. Next Steps:Work on DAT, Will be bale to self service evidence
7/11-Walkthrough Scheduled for 7/16/25
7/10/25-Recieved response from owner
7/9/25-Follow up emails sent to control owners and SMEs on 7/9 to schedule a walkthrough
7/3/25-Emails sent out to control owner/SME to schedule a walkthrough', 'Hayes, Sean (027443)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-07-03', '2025-07-31', '2025-07-30', '2025-07-30'),
    (81, 'VGCP-03636', 'A Vulnerability Management Policy is reviewed and approved annually to define vulnerability management requirements.', '8/6/2025 - DAT and OET were approved in Archer (JWM)
8/6/2025-DAT and OET uploaed into Archer
8/5/2025 - OET worksheet reviewed. Ready for Archer (JWM)
8/1/2025-Will complete OET on 8/4
7/31/2025-Starting OET 
7/30-DAT in Review
7/30/2025-Starting DAT today 
7/28/2025- We will test this control and pass it, VM team has remediated the issue. Will provide details of the observation in OET
7/22/2025-Cheryl discussed the policy review with Jake Webster, who was the previous owner of this control before Phil. Jake also considers it a failure. I will draft the issue and send it to Clara for review before forwarding it to the control owner and SME.
7/18-Cheryl had a conversation with Phil, they came to an undertanding. She is meeting with Jake Webster about this today and connect with me later.
7/16/25-Walkthtough completed. VM policy has not been reviewed for 2025, Phil and Pavel disagree with control failing. Phil and Cheryl will speak about this. I have spoken to Cheryl and I will wait for her direction after her discussion with Phil.
7/11-Walkthrough Scheduled for 7/16/25
7/10/25-Recieved response from owner
7/9/25-Follow up emails sent to control owners and SMEs on 7/9 to schedule a walkthrough
7/3/25-Emails sent out to control owner/SME to schedule a walkthrough', 'Crain, Phillip (194253)', 'Chris Shackleford for evidence', FALSE, 'Jason', 'NOT_STARTED', 'Walkthrough Scheduled', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-07-03', '2025-07-31', '2025-08-05', '2025-08-06'),
    (82, 'VGCP-05552', 'SWIFT Application IDs have their passwords rotated annually', '7/30/2025 - DAT and OET approved in Archer (JWM)
7/29/2025-DAT and OET uploaded into Archer
7/25/2025 - DAT and OET worksheets reviewed. Ready for Archer (JWM)
7/24-DAT and OET will be in review by EOD of 7/24
7/22-Working on DAT, Evidence has been gathered
7/16-Submitted SNOW request to gather ID Vault evidence of password changes
7/15/25-Walkthrough completed with Chris Swartz. Next steps: Work on DAT and gather evidence
7/11/25-Walktrhough scheduled for 7/15
7/10/25-Recieved response from owner
7/9/25-Follow up emails sent to control owners and SMEs on 7/9 to schedule a walkthrough
7/3/25-Emails sent out to control owner/SME to schedule a walkthrough', 'Sykes, John (014147)', 'Chris Swartz (include Joel Steinberg in email communications as well)', FALSE, 'Jason', 'COMPLETED', 'Testing In Progress', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-07-03', '2025-07-31', '2025-07-31', '2025-07-30'),
    (83, 'VGCP-00881', 'Information Destruction Policy review and approval', '7/1 sent kickoff email to Chris S and Doug J. both on PTO
7/7 reviewed DAT and OET, generated narrative and question documents, created teams folder structure, populated templates
7/8 scheduled walk-thru for 7/9
7/9 held walk thru. evidence due 7/16
7/10 DAT in review
7/11 working on OET
7/16 working on OET. need to talk to Chris S before completing
7/16 reached ou to Doug J. Looks like the process may have changed.
7/18 received answers from Doug. reviewing
7/22 Working DAT again Policy committee process changed.
7/22 DAT updated and back in review
7/23 working on OET
7/30 OET in review
7/31 OET ready for BP. addressing comments in DAT
7/31 OET uploaded to BP awaiting approval
8/1 addressing comments in DAT
8/1 comments addressed. DAT in review
8/18: Control assigned to Michael Hatch; discuss with Clara the current status of the conrol
8/19: OET in Archer waiting for approval. DAT has minor updates to be uploaded to Archer; need to discuss with Clara before uploading to Archer
8/21: Update DAT and submit for review by EOD today.
8/22: DAT has been updated based on feedback and is in review.
8/25: Uploaded DAT and OET to BP and ready for review. ', 'Cheryl Flannery', 'Chris Shackleford for evidence', FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-07-01', '2025-08-29', '2025-08-29', '2025-08-25'),
    (84, 'VGCP-05579', 'Enterprise Security and Fraud Policy Governance Committee', '7/1 sent kickoff email to Chris S and Doug J. both on PTO
7/7 reviewed DAT and OET, generated narrative and question documents, created teams folder structure, populated templates
7/8 scheduled walk-thru for 7/9
7/9 held walk thru. evidence due 7/16
7/10 DAT in review
7/11 working on OET
7/16 working on OET. need to talk to Chris S before completing
7/16 reached ou to Doug J. Looks like the process may have changed.
7/18 received answers from Doug. reviewing
7/22 Working DAT again Policy committee process changed.
7/22 DAT updated and back in review
7/23 working on OET
7/30 working on OET
8/1 addressing comments in DAT and working on OET
8/1 reached out to Chris S for help addressing comments.
8/18: Control assigned to Michael Hatch; discuss with Clara the current status of the conrol
8/19: DAT comment addressed and OET needs some clean up but in a good position to be put into review once MH meets with Clara.
8/21: Update OET and put into review by EOD today.
8/22: DAT and OET updated and in review
8/25: DAT and OET uploaded to BP for review.', 'Cheryl Flannery', 'Chris Shackleford for evidence', FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-07-01', '2025-08-29', '2025-08-29', '2025-08-25'),
    (85, 'VGCP-05584', 'Vanguard third-party procurement contract templates include terms related to information security requirements', '9/17/2025 - Approved in Archer (JWM)
9/15: Uploaded to Archer, waiting approval from JWM,
9/12/2025 - OET ready for Archer (JWM)
7/1 sent kickoff to Francie M.
7/8 Francie on PTO unitil 7/15. scheduling walk thru for week of 7/14
7/8 reviewing control prior to scheduling walk thru. created folders, questions, marrative doc, and card
7/9 scheduled walk thru for 7/17. Francie comes back from PTO 7/15
7/16 rescheduled to 7/18. control owner declined. Briefed Jack G on testing
7/18 control owner declined again. reschedule for 7
7/31 reschedule walkthru for 8/5
8/18: Control assigned to Michael Hatch; discuss with Clara the current status of the conrol
8/19: Need to schedule walkthrough and begin DATs and OETs
8/21: Conducted research and drafted narrative. Will set up walkthrough for next week.
8/25: Scheduled walkthrough for 8/26.
8/26: Conducted walkthrough, drafting DAT, requested evidence for OET
8/27: DAT reviewed and uploaded to Archer.
8/29: Discussed with control SME Megan Wadkins that she needs to extend due date to collect evidence to 9/8/25.
9/9: Follow up with Megan to get status of evidence.
9/10: Megan provided evidence, began OET, but she still is working on additional evidence
9/11: OET in review', 'McComb, Francie (063078)', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-07-01', '2025-09-30', '2025-09-16', '2025-09-16'),
    (86, 'VGCP-05586', 'Procurement Guidelines exist to outline the strategy for Supplier Lifecycle', '8/26 CW: Unmapped and retired control
7/1 searching for control owner. contacting ESM
7/8 contact out of office until 7/14. Still trying to determine control owner. No response from procurement group email.
7/14 Jennifer B recommended reachout to Rick Kramerr. Reached out to Risk Kramer.
7/16 Clara mentioned in meeting that this may not be ES&F. waiting to find out
7/31 followed up to get update on path forward from John, Clara, Jen
8/18: Control assigned to Michael Hatch; discuss with Clara the current status of the conrol
8/19: Discuss control owner with Clara
8/20: Clara to confirm if control is in scope
8/21: Discuss update with Clara to confirm if control is in scope.', 'Tester to identify owner', NULL, FALSE, 'Mark', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-30', NULL, '2025-08-26'),
    (87, 'VGCP-05608', 'SWIFT SIEM rules are created and monitored through a formal process', '7/30: OET loaded to BP and ready for approval
7/29 CW: DAT approved in BP. OET reviewed and ready for BP
7/28: OET comments addressed and sent back for review
7/18: Submitted OET for review
7/16: walkthrough held with CSOC, awaiting evidence from Cheryl
7/15: Submitted DAT for review
7/10: Received updated information for DAT, making revisions on narrative
7/9: Received evidence from Cheryl to support the operating test
7/1: DAT sent and under review by Cheryl
7/1: Email requesting evidence and walkthrough mtg scheduled - 7/16
6/30: SNOW ticket opened for mtg request', 'Reitnauer, Jonathan (030822)', 'Christina Duke/Cheryl Texter', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-07-01', '2025-07-31', '2025-07-31', '2025-07-31'),
    (88, 'VGCP-05609', 'SWIFT SIEM rules are recertified annually through a formal process', '7/30: DAT loaded into BP and ready for approval
7/29 CW: DAT reviewed and ready for BP
7/29: OET loaded into BP and ready for approval
7/28: Revisions made to DAT, sent back for review
7/18: Submitted OET for review
7/18: resubmitted DAT with revised wording, ready for review
7/17: proposed revision to DAT sent to Cheryl for review
7/16: walkthrough held with CSOC, awaiting evidence from Cheryl
7/15: Submitted DAT for review
7/10: Received updated information for DAT, making revisions on narrative
7/1: DAT sent and under review by Cheryl
7/1: Email requesting evidence and walkthrough mtg scheduled - 7/16
6/30: SNOW ticket opened for mtg request', 'Reitnauer, Jonathan (030822)', 'Christina Duke/Cheryl Texter', FALSE, 'Sara', 'IN_REVIEW', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'IN_REVIEW', '2025-07-01', '2025-07-31', '2025-07-31', '2025-07-31'),
    (89, 'VGCP-06736', 'SIEM rules are created through a formal process', '7/30: revisions made and DAT loaded to BP for approval
7/29 CW: DAT ready for review. Let''s wait for the CSOC meeting to occur first before anything is approved in Archer (DAT and OET)
7/29: OET loaded to BP and ready for approval
7/28: Revisions made to DAT and sent to Cheryl Texter and Clara for review
7/18: Submitted OET for review
7/16: walkthrough held with CSOC, awaiting evidence from Cheryl
7/15: Submitted DAT for review
7/10: Received updated information for DAT, making revisions on narrative
7/1: DAT sent and under review by Cheryl
7/1: Email requesting evidence and walkthrough mtg scheduled - 7/16
6/30: SNOW ticket opened for mtg request', 'Reitnauer, Jonathan (030822)', 'Christina Duke/Cheryl Texter', FALSE, 'Sara', 'IN_REVIEW', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'IN_REVIEW', '2025-07-01', '2025-07-31', '2025-07-31', '2025-07-31'),
    (90, 'VGCP-06737', 'SIEM rules are recertified annually through a formal process', '7/31: DAT submitted to BP for approval
7/30: OET submitted to BP and ready for approval, DAT revisions made and ready for review
7/29 CW: OET reviewed and ready for BP
7/28: Questions to Cheryl Texter for DAT clarification
7/28: Submitted OET for review
7/16: walkthrough held with CSOC, awaiting evidence from Cheryl
7/15: Submitted DAT for review
7/10: Received updated information for DAT, making revisions on narrative
7/1: DAT sent and under review by Cheryl
7/1: Email requesting evidence and walkthrough mtg scheduled - 7/16
6/30: SNOW ticket opened for mtg request', 'Reitnauer, Jonathan (030822)', 'Christina Duke/Cheryl Texter', FALSE, 'Sara', 'IN_REVIEW', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'IN_REVIEW', '2025-07-01', '2025-07-31', '2025-07-31', '2025-07-31'),
    (91, 'VGCP-06907', 'SWIFT lookup tables are recertified annually through a formal process', '7/30: OET loaded to BP and ready for approval
7/29 CW: DAT approved in BP. OET reviewed and ready for BP
7/29: Entered DAT into BP for approval
7/28: Submitted OET for review
7/16: walkthrough held with CSOC, awaiting evidence from Cheryl
7/15: Submitted DAT for review
7/10: Received updated information for DAT, making revisions on narrative
7/1: DAT sent and under review by Cheryl
7/1: Email requesting evidence and walkthrough mtg scheduled - 7/16
6/30: SNOW ticket opened for mtg request', 'Reitnauer, Jonathan (030822)', 'Christina Duke/Cheryl Texter', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-07-01', '2025-07-31', '2025-07-31', '2025-07-31'),
    (92, 'VGCP-03421', 'An Authentication Framework is in place for Vanguards externally facing client applications', '7/31/2025 - OET approved in Archer
7/31/2025-OET uploaded into Archer
7/30/2025 - OET worksheet reviewed. Ready for Archer (JWM)
7/30/2025 - DAT approved in Archer
7/29/2025-DAT uploaded into Archer
7/28/2025-OET in Review
7/25/2025 - DAT worksheet reviewed. Ready for Archer (JWM)
7/24-Will begin working on DAT on 7/24
7/18- Will talk to Clara about this. The Authentication Framework is not a policy and there is no requirement for it to be reviewed annually. We should be able to test this.
7/16/25-Walkthrough completed, Next steps: Authentication Framework was not reviewed in 2024, This might be an issue, Craig Agrees, Will have to write Issue and send it over to Craig and Control owner.
7/11/25-Walkthrough scheduled for 7/16
7/9/25-Follow up emails sent to control owners and SMEs on 7/9 to schedule a walkthrough
7/3/25-Emails sent out to control owner/SME to schedule a walkthrough', 'Walker, Scott (052612)', 'Craig Murray', FALSE, 'Jason', 'COMPLETED', 'Walkthrough Completed', 'COMPLETED', 'Testing In Progress', 'COMPLETED', '2025-07-03', '2025-07-31', '2025-07-30', '2025-07-31'),
    (93, 'VGCP-08070', 'Cloud vulnerability Issues are rated for risk according to predefined criteria.', '9/19 CW: DAT reviewed with comments
8/25- DAT and OET is in review
8/22- I will submit in Archer based on comments from Bernard
8/21 - Waiting for comments from Bernard
8/19- Working on OET''s
8/18- Working on OET''s
8/15- In review 
8/14- I will submit for review 
8/13- Addressing the comments 
8/12-  Working on rewritting DAT as directions from Clara.
8/11- I will respond to the DAT according to Clara''s comments
8/8 - DAT is in review and I will submit in Archer once approved
8/7 - Waiting for the feedback on DAT and working on OET
8/6-Waiting for feedback on DAT
8/5 - Submitted for DAT review
8/4 - I will submit DAT for review today.
8/1 -Making changes to the DAT
7/31 -  Estimated DAT to be put into review by next week
7/30 - I will make changes to the DAT according to Wong''s feedback 
7/29 - DAT Is in review with additional comments
7/28 - Updated DAT with additional information
7/25- DAT in review
7/24- Updated planner board and updated DAT in annual control testing folder
7/23- Working on DAT notes
7/22- DAT in progress and gathering evidence
7/21 - going through confluence links
7/18 - Gathering evidence and screenshots
7/17 - Walkthrough scheduled on 7/17 at 12:30 PM EST
7/15 - Requested access to the confluence links
7/11 - Sent email to the owner', 'Matskevich, Pavel (056961)', 'Venkat Putluri, Aaron Burgess', FALSE, 'Avinash', 'IN_PROGRESS', 'Addressing Comments', 'IN_REVIEW', NULL, 'IN_PROGRESS', '2025-07-11', '2025-09-05', '2025-09-05', NULL),
    (94, 'VGCP-08071', 'Cloud vulnerability Findings are rated for risk according to predefined criteria.', '9/19 CW: DAT reviewed with comments
8/25- DAT and OET is in review
8/22- I will submit in Archer based on comments from Bernard
8/21 - Waiting for comments from Bernard
8/19- Working on OET''s
8/18- Working on OET''s
8/15- In review 
8/14- I will submit for review 
8/13- Addressing the comments 
8/12-  Working on rewritting DAT as directions from Clara.
8/11- I will respond to the DAT according to Clara''s comments
8/8 - DAT is in review and I will submit in Archer once approved
8/7 - Waiting for the feedback on DAT and working on OET
8/6-Waiting for feedback on DAT
8/5 - Submitted for DAT review
8/4 - I will submit DAT for review today.
8/1 -Making changes to the DAT
7/31 -  Estimated DAT to be put into review by next week
7/30 - I will make changes to the DAT according to Wong''s feedback 
7/29 - DAT Is in review with additional comments
7/28 - Updated DAT with additional information
7/25- DAT in review
7/24- Updated planner board and updated DAT in annual control testing folder
7/23- Working on DAT notes
7/22- DAT in progress and gathering evidence
7/21 - going through confluence links
7/18 - Gathering evidence and screenshots
7/17 - Walkthrough scheduled on 7/17 at 12:30 PM EST
7/15 - Requested access to the confluence links
7/11 - Sent email to the owner', 'Matskevich, Pavel (056961)', 'Dave Levengood', FALSE, 'Avinash', 'IN_PROGRESS', 'Addressing Comments', 'IN_REVIEW', NULL, 'IN_PROGRESS', '2025-07-11', '2025-09-05', '2025-09-05', NULL),
    (95, 'VGCP-08072', 'Cloud vulnerabilities that cannot be remediated or remediated within SLA follow a formal acceptance process.', '9/19 CW: Reviewed and added back missing comments.
8/25- sent to the final review
8/22- I will submit in Archer based on comments from Bernard
8/21 - Waiting for comments from Bernad
8/19 - Working on OET''s
8/18- Working on OET''s
8/15- I will submit for review
8/14- Working on rewritting DAT
8/13- Addressing the comments 
8/12-  Working on rewritting DAT as directions from Clara.
8/11- I will respond to the DAT according to Clara''s comments
8/8 - DAT is in review and I will submit in Archer once approved
8/7 - Waiting for the feedback on DAT and working on OET
 8/6 - waiting for the feedback on DAT
8/5 - Submitted for DAT review
8/4 - I will submit DAT for review today.
8/1 -Making changes to the DAT
7/31 - Working on DAT and to be put for review by next week.
7/30 -  I will make changes to the DAT according to Wong''s feedback 
7/29 - DAT Is in review with additional comments
7/28 - Updated DAT with additional information
7/25 - DAT in review
7/24 - Updated planner board and updated DAT in annual control testing folder
7/23- Working on DAT notes
7/22- DAT in progress
7/21 - DAT in progress and gathering evidence
7/18 - Need other walkthrough meeting to be scheduled on 7/21
7/17 - Walkthrough scheduled on 7/17 at 12:30 PM EST
7/15 - Requested access to the confluence links
7/11 - Sent email to the owners', 'Matskevich, Pavel (056961)', 'Dave Levengood', FALSE, 'Avinash', 'IN_PROGRESS', 'Addressing Comments', 'IN_REVIEW', NULL, 'IN_PROGRESS', '2025-07-11', '2025-09-05', '2025-09-05', NULL),
    (96, 'VGCP-01054', 'The Technical Security Advisors team provides quarterly vulnerability risk reports to the CISO senior management.', '10/3/2025-Pulling this back into progress per conversation with Clara we will be expanding the testing period. Will include Q3 reports in test. September Report and CISO Aknowledgement has not been uploaded into the Confluence page. Will reach out to Jason Lemonds to see when that will happen.
9/15/2025-OET has been completed for this control. I will be meeting with Bernie and Jason Lemonds to discuss possible enhancements or changes to what we test for in this control.
8/29/2025-Jason Lemonds does not like the idea of more feedback from the CISO on posture reports. WIll discuss with Bernie on this.
8/26/2025-OET in review
8/22/2025- Will start working on OET today. WIll set up call today for nextweek between Clara, Bernie and I to discuss this control as well. 
8/20/2025- Will speak to Clara about this. No Q1 Risk report due to change of direction with SLAs
8/15/25-Walkthrough complete
8/8/25- Walkthrough scheduled for 8/15/25
8/6/25- Emails sent out to Control owner/SME for a walkthrough ', 'Lemonds, Jason (040194)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'IN_REVIEW', 'Testing In Progress', 'IN_REVIEW', NULL, '2025-08-29', '2025-08-29', NULL),
    (97, 'VGCP-05483', 'An ad hoc vulnerability scan profile is defined in a standardized procedure.', '8/21/2025 - OET Approved in Archer (JWM)
8/20/2025 - DAT Approved in Archer (JWM)
8/20/25-OET uploaded in Archer
8/18/2025 - DAT and OET ready for Archer (JWM)
8/15/2025-OET in review
8/15-Will begin working on OET
8/13/25-DAT in review
8/13/25-Working on DAT
8/8/25-Walkthrough complete
8/6/25- Emails sent out to Control owner/SME for a walkthrough ', 'Kushari, Dip (018642)', NULL, FALSE, 'Jason', 'COMPLETED', NULL, 'COMPLETED', NULL, 'COMPLETED', NULL, '2025-08-29', NULL, '2025-08-21'),
    (98, 'VGCP-06896', 'Multifactor Authentication is enforced for all outgoing money movement transactions and for any changes made to high-risk data made by a client', '9/2/2025 - OET approved in Archer (JWM)
9/2/2025-OET uploaded into Archer
9/2/2025 - OET reviewed. Ready for Archer (JWM)
8/28/2025 - DAT approved in Archer (JWM)
8/27/2025-OET in Review
8/25/2025-DAT uploaded in Archer
8/25/2025 - DAT ready for Archer (JWM)
8/21/25-Followed up with Malcolm and he will have evidence to me Monday Morning
8/19/25-Malcolm needs a couple more days to get evidence back to me
8/19/25-DAT in review
8/19/25- Working on DAT
8/14/25-Walkthrough complete
8/8/25-Walkthrough scheduled for 8/14/25
8/6/25- Emails sent out to Control owner/SME for a walkthrough ', 'Scott, Mason (064291)', 'Malcolm Chau', FALSE, 'Jason', 'COMPLETED', NULL, 'COMPLETED', NULL, 'COMPLETED', NULL, '2025-08-29', '2025-08-29', '2025-09-02'),
    (99, 'VGCP-06911', 'A Fraud and Corruption Control Plan exists to outline VIAs fraud and corruption control approach and is reviewed annually', '9/2/2025 - OET approved in Archer (JWM)
9/2/2025_OET uploaded into Archer
9/2/2025 - OET reviewed. Ready for Archer. (JWM)
8/28/2025 - DAT Approved in Archer (JWM)
8/25/2025-DAT Uploaded in Archer
8/25/2025-OET in review
8/25/25- OET is back in progress and will be in review today
8/25/2025 - DAT ready for Archer (JWM)
8/22/25-Working on completing the OET today
8/20/2025-DAT in review
8/18/25-Walkthrough Complete
8/14/25-Vic Kwong had to reschedule our walkthrough for 8/18/25
8/8/25-Walkthrough scheduled for 8/14/25
8/6/25- Emails sent out to Control owner/SME for a walkthrough ', 'Scott, Mason (064291)', 'Malcolm Chau', FALSE, 'Jason', 'COMPLETED', NULL, 'COMPLETED', NULL, 'COMPLETED', NULL, '2025-08-29', '2025-08-27', '2025-09-02'),
    (100, 'VGCP-05753', 'Information security leadership and major programs responsibilities defined', '8/27: DAT reviewed and uploaded to Archer.
8/26: Conducted walkthrough, drafting DAT. OET will be put on hold until board meeting occurs to review and approve the defined RnR (~November 2025).
8/25: Scheduled walkthrough for 8/26.
8/21: Conducted research and drafted narrative. Will set up walkthrough for next week. Concern around Cheryl being OOO.
8/19: Confirm if David Jacobs is the control owner', 'Cheryl Flannery', 'Jack Galante', FALSE, 'Michael', 'COMPLETED', 'Testing Completed', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', '2025-12-01', NULL),
    (101, 'VGCP-06565', 'Global Security partners with the various service providers for travel security and threat intelligence.', '9/15: OET in review
9/9: OET in progress, requested additional evidence, waiting for a response
9/8: Recieved evidence from Katie Kercher and have started drafting OET.
9/3: Control SME Katie Kercher confirmed she recieved my follow up email and is working on the evidence
9/2/2025: DAT Approved in Archer (JWM)
9/2: Sent follow up email on 9/2 to collect evidence for control. Uploaded DAT to Archer.
8/29: Waiting for evidence. Will send follow up email to collect evidence on 9/2.
8/27: DAT completed and sent email request for OET.
8/25: Walkthrough scheduled 8/27.
8/21: Conducted research and drafted narrative. Will set up walkthrough for next week.
8/19: Confirm if John Krieg is the control owner', 'Krieg, John (003930)', NULL, FALSE, 'Michael', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-30', '2025-09-19', '2025-09-17'),
    (102, 'VGCP-06567', 'ES&F Global Enterprise Security / Governance, Risk and Control team has a CyberReg team which focuses on legal or regulatory requirements for cybersecurity.', '9/16: Uploaded OET to Archer
9/15: OET in review
9/10: John to provide evidence by 9/12
9/4: DAT uploaded to Archer for review
9/3: DAT in review and sent email to collect evidence
9/2: Completed walkthrough, drafting DAT and will send email to collect evidence.
8/27: Walkthrough scheduled on 8/29.
8/25: Validating John can be the control owner as this would break the rule of a manger owning the control.
8/21: Conducted research and drafted narrative. Will set up walkthrough for next week.
8/19: Confirm if John Murphy is the control owner', 'John Murphy', 'John Murphy', FALSE, 'Michael', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-30', '2025-09-24', '2025-09-17'),
    (103, 'VGCP-06568', 'The CyberReg function receives key information from various stakeholders related to legal and regulatory requirements.', '9/16: Uploaded OET to Archer
9/15: OET in review
9/10: John to provide evidence by 9/12
9/4: DAT uploaded to Archer for review
9/3: DAT in review and sent email to collect evidence
9/2: Completed walkthrough, drafting DAT and will send email to collect evidence.
8/27: Walkthrough scheduled on 8/29.
8/25: Validating John can be the control owner as this would break the rule of a manger owning the control.
8/21: Conducted research and drafted narrative. Will set up walkthrough for next week.
8/19: Confirm if John Murphy is the control owner', 'John Murphy', 'John Murphy', FALSE, 'Michael', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-30', '2025-09-24', '2025-09-17'),
    (104, 'VGCP-01170', 'A post-mortem, including lessons learned, is conducted for all declared security incidents.', '8/27: DAT and OET uploaded into Archer
8/22: Comments addressed and re-submitted for review
8/19: OET submitted for review
8/18: reviewing and responding to DAT comments
8/12: Submitted DAT for review
8/12: Met with CSOC for walkthrough
8/5: Evidence gathering email sent for walkthrough conversation on 8/12
8/4: Created cards in planner and files in teams
8/1: Walkthrough scheduled for 8/12
8/1: SNOW ticket opened for mtg request', 'Schellhammer, Robert (018822)', 'Christina Duke', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-08-01', '2025-08-29', '2025-08-29', '2025-08-27'),
    (105, 'VGCP-05613', 'Detected events are rated for impact based on established criteria', '9/12: Submitted for final approval in BP
9/12: resubmitted DAT/OET for review, incorporating CSOC feedback from meeting
9/9: follow up meeting with CSOC scheduled for 9/12
9/5: Email sent to Jonathan R to gain clarity on one of his controls and potentially combine 5613 & 6736
9/2: Follow up meeting scheduled for 9/4
8/29: Sent follow up email with questions to CSOC
8/19: OET submitted for review
8/18: reviewing and responding to DAT comment
8/12: Submitted DAT for review
8/12: Met with CSOC for walkthrough
8/5: Evidence gathering email sent for walkthrough conversation on 8/12
8/4: Created cards in planner and files in teams
8/1: Walkthrough scheduled for 8/12
8/1: SNOW ticket opened for mtg request', 'Schellhammer, Robert (018822)', 'Christina Duke', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-08-01', '2025-08-29', '2025-09-12', '2025-09-12'),
    (106, 'VGCP-05611', 'An Insider Threat Protection Program is established to detect, prevent, or respond to insider threats.', '9/9: revisions made and resubmitted for review
9/4: Re-submitted for review
8/29: On-hold - Waiting for next steps from Brendan/Clara
8/26: Revised DAT and OET sent to Clara for review
8/26: Sent revised DAT narrative to CSOC for review, received updated evidence for OET and making revisions accordingly
8/25: Meeting with CSOC for clarification
8/19: OET submitted for review
8/18: reviewing and responding to DAT comments
8/12: Submitted DAT for review
8/12: Met with CSOC for walkthrough
8/5: Evidence gathering email sent for walkthrough conversation on 8/12
8/4: Created cards in planner and files in teams
8/1: Walkthrough scheduled for 8/12
8/1: SNOW ticket opened for mtg request', 'Bourne, Richard (013534)', 'Christina Duke', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-08-01', '2025-08-29', '2025-09-12', '2025-09-11'),
    (107, 'VGCP-06695', 'Vulnerabilities are rated for risk according to predefined criteria.', '9/22: OET uploaded to Archer - MH
9/17: OET in review - MH  
9/15: DAT uploaded to Archer, OET in progress, waiting for Dave to send evidence. - MH  
9/11- Dave to Send OET''s back by Monday - MH  
9/4: DAT completed and is in review.- MH  
8/27- Dave will send confluence links 
8/26 - rescheduled meeting on 8/26 due to unavailablity of the control SME
8/20- rescheduled meeting on 8/25
8/18 - Rescheduled meeting on 8/19
8/13 - Scheduled Walkthrough meeting on 8/15 
8/7 - I will start working on DAT
8/1- I will start working on this control next week', 'Matskevich, Pavel (056961)', 'Dave Levengood', FALSE, 'Avinash', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-12', '2025-09-26', '2025-09-26'),
    (108, 'VGCP-06696', 'Assets excluded from vulnerability scanning are reviewed and approved through a formal process', '9/23: OET uploaded to Archer
9/22: OET in review
9/22: Requested access to Snow to test evidence on 9/16 to test vulnerabilities. Our request has been rejected on 9/19 by Brad Fischer. We are unable to test the control without access to SNow - MH
9/15: DAT uploaded to Archer, OET in progress, waiting for Dave to send evidence. - MH  
9/11- Dave to Send OET''s back by Monday - MH  
9/4: DAT completed and is in review.- MH  
8/27- Dave will send confluence links 
8/26 - rescheduled meeting on 8/26 due to unavailablity of the control SME
8/20- rescheduled meeting on 8/25
8/18 - Rescheduled meeting on 8/19
8/13 - Scheduled Walkthrough meeting on 8/15 
8/7 - I will start working on DAT
8/1- I will start working on this control next week', 'Matskevich, Pavel (056961)', 'Dave Levengood', FALSE, 'Avinash', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-12', '2025-09-26', '2025-09-26'),
    (109, 'VGCP-06697', 'Vulnerabilities that cannot be remediated or remediated within SLA follow a formal exception process.', '9/23: OET uploaded to Archer
9/22: Addreessing comments from Clara, needed to reach out to Dave to get additional information for testing.
9/17: OET in review - MH  
9/11- Dave to Send OET''s back by Monday - MH  
9/4: DAT completed and is in review. - MH  
8/27- Dave will send confluence links 
8/26 - rescheduled meeting on 8/26 due to unavailablity of the control SME
8/20- rescheduled meeting on 8/25
8/18 - Rescheduled meeting on 8/19
8/13 - Scheduled Walkthrough meeting on 8/15 
8/7 - I will start working on DAT
8/1- I will start working on this control next week', 'Matskevich, Pavel (056961)', 'Dave Levengood', FALSE, 'Avinash', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-12', '2025-09-30', '2025-09-26'),
    (110, 'VGCP-06698', 'Assets excluded from vulnerability scanning are scanned semi-annually', '9/23: OET ready for Archer, DAT waiting for approval from Dave on reccomendation, Dave said he can provide his approval on 9/24 after he reviews with Pavel
9/22: OET in review
9/22: Discussed with Clara and Vivek on potential desgin gap and sent email to control owner providing our reccomendation to see if they agree.
9/17: Working to update DAT based on feedback, OET not started
9/11- Dave to Send OET''s back by Monday - MH  
9/4: DAT completed and is in review. - MH  
8/27- Dave will send confluence links 
8/26 - rescheduled meeting on 8/26 due to unavailablity of the control SME
8/20- rescheduled meeting on 8/25
8/18 - Rescheduled meeting on 8/19
8/13 - Scheduled Walkthrough meeting on 8/15 
8/7 - I will start working on DAT
8/1- I will start working on this control next week', 'Matskevich, Pavel (056961)', 'Dave Levengood', FALSE, 'Avinash', 'COMPLETED', 'Addressing Comments', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-12', '2025-09-30', NULL),
    (111, 'VGCP-06699', 'Assets excluded from routine and semi-annually vulnerability scanning are documented as risks and recertified twice every year.', '9/17: OET uploaded to Archer waiting for review and approval - MH  
9/16: OET in review - MH  
9/15: DAT uploaded to Archer, OET in progress, waiting for Dave to send evidence. - MH  
9/11- DAT completed and is in review and OET''s will be ready by Monday - MH  
9/5: Working on DAT - MH  
8/27- Scheduled call on 8/28 for an hour
8/26 - rescheduled meeting on 8/26 due to unavailablity of the control SME
8/20- rescheduled meeting on 8/25
8/18 - Rescheduled meeting on 8/19
8/13 - Scheduled Walkthrough meeting on 8/15 
8/7 - I will start working on DAT
8/1- I will start working on this control next week', 'Matskevich, Pavel (056961)', 'Dave Levengood', FALSE, 'Avinash', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', NULL, '2025-09-12', '2025-09-19', '2025-09-19'),
    (112, 'VGCP-05366', ' Users are removed from Cisive in a timely manner following UARs and terminations', '9/16/2025-DAT is Uploaded to BP
9/12/2025-DAT is in review
9/11/25-Evidence recieved
9/4/2025-Walkthrough Completed
8/29/2025-Walkthrough scheduled for 9/4/2024
8/26/2025-Emailed control owner to schedule walkthrough ', 'Krieg, John (003930)', NULL, FALSE, 'Jason', 'IN_REVIEW', 'Testing In Progress', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', '2025-09-29', NULL),
    (113, 'VGCP-05367', 'VGCP-05367: Global Security meets with Cisive every two weeks to provide updates and to notify the team of any changes.', '9/23/2025-OET uploaded to Archer
9/19/2025-Commnets addressed, OET back in review
9/17/2025-OET in review
9/16/2025-DAT uploaded to BP
9/11/25-Evidence Recieved
9/10/2025-DAT in review
9/4/2025-Walkthrough Completed
8/29/2025-Walkthrough scheduled for 9/4/2024
8/26/2025-Emailed control owner to schedule walkthrough ', 'Krieg, John (003930)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-09-12', '2025-09-30', '2025-09-26', '2025-09-22'),
    (114, 'VGCP-05805', 'A nine-day bank hold is applied after changes are made to a client''s account details', '9/30/25-OET uploaded to BP
9/23/2025-OET in review
9/22/2025-Working on OET
9/16/2025-DAT uploaded into BP', 'Scott, Mason (064291)', 'Malcolm Chau', FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-09-12', '2025-09-30', '2025-09-28', '2025-09-30'),
    (115, 'VGCP-06779', 'Personal Investor IDPS accounts restricted to a maximum of one (1) external bank account linked to cash hub at any time', '10/3/2025-Walkthrough Scheduled for 10/8 with Malcolm 
8/28/2025-WIll test this control in October', 'Scott, Mason (064291)', 'Victor Kwong', FALSE, 'Jason', 'NOT_STARTED', 'Walkthrough Completed', 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, '2025-09-30', NULL, NULL),
    (116, 'VGCP-05368', 'Vanguard is responsible for managing Vendor adherence to the terms and conditions stated within their service agreements with Cisive.', '10/3/2025-Walkthrough scheduled for 10/8. Waiting for control owner and SME to accept', 'Krieg, John (003930)', NULL, FALSE, 'Jason', 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, '2025-10-31', NULL, NULL),
    (117, 'VGCP-05369', 'Vanguard reviews results of Cisive''s background checks immediately upon notification. Vanguard relies on Cisive to have effective controls surrounding data accuracy.', '10/3/2025-Walkthrough scheduled for 10/8. Waiting for control owner and SME to accept', 'Krieg, John (003930)', NULL, FALSE, 'Jason', 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, '2025-10-31', NULL, NULL),
    (118, 'VGCP-05370', 'All PII entered into Cisive is reviewed for accuracy and any discrepancies identified are communicated and revised as necessary.', '10/3/2025-Walkthrough scheduled for 10/8. Waiting for control owner and SME to accept', 'Krieg, John (003930)', NULL, FALSE, 'Jason', 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, '2025-10-31', NULL, NULL),
    (119, 'VGCP-05379', 'All outbound e-mails sent to Cisive from Vanguard are appropriately protected and monitored', '9/22/2025-DAT in Archer
9/12/2025-DAT is in review
9/11/25-Working on DAT
9/11/25-Evidence recieved
9/4/25-Walkthrough Completed
8/29/2025-Walkthrough scheduled for 9/4/2025
8/26/2025-Emailed control owner to schedule walkthrough ', 'Krieg, John (003930)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-09-01', '2025-10-31', '2025-09-26', '2025-09-24'),
    (120, 'VGCP-04987', 'Logging and tracking for potential fraud at personal.vanguard.com are in place.', '10/6 - met with Marianna, received overview of detective monitors. To schedule meeting with Joe and follow-up on ownership.
10/1 -meeting with Marianna Friday to review fraud monitoring reports
9/16 - meeting setup with Marianna Szbazo, Pooja Manuja, and Brett Matlack on 9/24 to discuss details on new fraud monitoring processes and ownership.
8/25 - Coordinating with Marianna on new control ownership/SME. Will need to substantially update narrative.
8/20 - followed-up with Marianna
8/14 - Reached out to Marianna Szabo for new control owner', 'Zajac, Christian (158403)', NULL, TRUE, 'Brendan', 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, 'NOT_STARTED', NULL, '2025-10-31', '2025-10-30', NULL),
    (121, 'VGCP-05784', 'An annual table-top exercise (TTX) is conducted of a scenario-based security event and action items are documented to address uncovered gaps.', '9/22: DAT and OET loaded to Archer for approval
9/16: OET submitted for review
9/12: DAT submitted for review
9/2: Evidence gathering email sent
8/25: Set up files and cards in teams
8/25: Walkthrough scheduled for 9/11
8/20: SNOW ticket opened for mtg request', 'Schellhammer, Robert (018822)', 'Christina Duke ', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-08-20', '2025-09-30', '2025-09-30', '2025-09-22'),
    (122, 'VGCP-05209', 'NACHA - A Web Application Firewall is in place to mitigate attacks against the Personal Investor Website', '9/18: DAT and OET loaded to archer
9/16: OET submitted for review
9/12: DAT submitted for review
9/2: Evidence gathering email sent
8/25: Set up files and cards in teams
8/25: Walkthrough scheduled for 9/11
8/20: SNOW ticket opened for mtg request', 'Quinn, Seamus (029385)
Bill Wloczewski', 'Christina Duke ', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-08-20', '2025-09-30', '2025-09-30', '2025-09-18'),
    (123, 'VGCP-04988', 'NACHA - Physical Security controls exist at Vanguard Data Centers and are evaluated annually for effectiveness', '9/19: OET loaded to Archer
9/18: OET submitted for review
9/17: DAT loaded to Archer
9/10: DAT submitted for review
9/9: Walkthrough completed and emails sent for evidence gathering
9/2: Walkthrough scheduled for 9/9
8/29: Send intro email for testing awareness
8/25: Set up files and cards in teams
8/21: proposed DAT narrative sent to Clara for feedback
8/14 - Per scrum update, Ownership has changed from Peter to Scott MacDougall(BE)', 'Kowenhoven, Peter (158384)
Scott MacDougall - John Kreig', 'John Kreig', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-08-21', '2025-09-30', '2025-09-30', '2025-09-19'),
    (124, 'VGCP-05912', 'NACHA - A process exists where new or updated accounts are validated before WEB debits can occur', '9/22: DAT loaded to archer for approval
9/19: OET loaded to archer
9/18: OET and DAT submitted for review
9/10: Walkthrough completed and evidence requested by 9/17
8/29: Walkthrough scheduled for 9/10
8/27: New control owner identified - Carly Snider
8/27: Sent introductory email to control owner
8/25: Set up files and cards in teams
8/21: Proposed narrative revisions sent to Clara for input/revisions', 'Forkner, Nathan (025192) 
Carly Snider', 'Spencer Stanley', FALSE, 'Sara', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-08-21', '2025-09-30', '2025-09-30', '2025-09-22'),
    (125, 'VGCP-00010', 'Business Impact Assessments (BIAs) are required for all new applications and when existing systems are upgraded.', '9/19 - DAT by BE, returned with comments.
9/10 - DAT is in review and OET will be completed by  9/21', 'Minnes, Matthew (198076)', 'Jeffrey Solis ', FALSE, 'Avinash', 'IN_REVIEW', 'Testing Completed', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', NULL, NULL),
    (126, 'VGCP-04985', 'NACHA - IT Application Security assessments are performed periodically and at consistent intervals to identify any new vulnerabilities that are dispositioned in accordance with Vanguard requirements.', '9/23 - DAT by BE, returned with comments.
9/10 - DAT is in review and OET will be completed by  9/21', 'Minnes, Matthew (198076)', 'Susan Wojdula', FALSE, 'Avinash', 'IN_REVIEW', 'Testing Completed', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', NULL, NULL),
    (127, 'VGCP-05588', 'A risk assessment methodology and program exists to determine the testing frequency of assets', '9/24 - DAT by BE, returned with comments.
9/10 - DAT is in review and OET will be completed by  9/21', 'Minnes, Matthew (198076)', 'Sharey Haque', FALSE, 'Avinash', 'IN_REVIEW', 'Testing Completed', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', NULL, NULL),
    (128, 'VGCP-05675', 'A risk assessment methodology and program exists to determine how risks are to be treated', '9/24 - DAT by BE, returned with comments.
9/10 - DAT is in review and OET will be completed by  9/21', 'Minnes, Matthew (198076)', 'Michael Townsend', FALSE, 'Avinash', 'IN_REVIEW', 'Testing Completed', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', NULL, NULL),
    (129, 'VGCP-04980', 'NACHA - Vanguard maintains architecture diagrams for infrastructure hosting personal.vanguard.com and client bank instruction information.', '9/23 - DAT by BE, returned with comments.
9/17- DAT will be submitted by 9/18 EOD
9/12 - Scheduled meeting with control owner on Monday (9/15)', 'Thomas, Shibu (030392)', NULL, FALSE, 'Avinash', 'IN_REVIEW', 'Testing Completed', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', NULL, NULL),
    (130, 'VGCP-04989', 'Access to DB2 tables containing banking instruction data follows the enterprise process.', '9/23 - DAT by BE, returned with comments.
9/17 - DAT will be submitted by 9/18 EOD
9/12 - Working on DAT', 'Dolski, Brian (017760)', NULL, FALSE, 'Avinash', 'IN_REVIEW', 'Testing Completed', 'IN_PROGRESS', 'Testing In Progress', 'IN_PROGRESS', NULL, '2025-09-30', NULL, NULL),
    (131, 'VGCP-03656', 'A network reconciliation is conducted to detect networks missing from Qualys and remediate the discrepancies to support breadth-of-coverage.', '9/10/205-Will schedule meeting with DIP Kushari about today about this control. Will let Brendan know when I do.
9/9: Brendan meeting with Jason to discuss next steps for this control. This control will fail at design, referencing ISS-18497. No OET will be completed.', 'Kushari, Dip (018642)', NULL, FALSE, 'Jason', 'COMPLETED', 'Testing Completed', 'COMPLETED', 'Testing Completed', 'COMPLETED', '2025-09-09', '2025-09-30', '2025-09-30', '2025-09-30')
),
-- Insert controls and keep deterministic ordering (by ref)
ins_controls AS (
  INSERT INTO controls (vgcpid, description, control_owner, control_sme, escalation, last_tested)
  SELECT
    s.vgcpid,
    s.notes,
    COALESCE(s.control_owner, 'Unknown') AS control_owner,
    COALESCE(s.control_sme, 'N/A') AS control_sme,
    s.escalation::boolean,
    s.date_completed::date
  FROM src s
  ORDER BY s.ref
  RETURNING control_id
),
-- Insert requests in the same order as controls so row_number pairing is stable
ins_requests AS (
  INSERT INTO requests (requestor, start_date, due_date, complete_date, status, created_by)
  SELECT
    COALESCE(s.control_owner, 'Unknown') AS requestor,
    s.date_started::date,
    COALESCE(s.due_date::date, current_date + interval '30 days') AS due_date,
    s.date_completed::date,
    s.request_status::request_status,
    (SELECT user_id FROM users WHERE role='MANAGER'::user_role ORDER BY user_id LIMIT 1)
  FROM src s
  ORDER BY s.ref
  RETURNING request_id
),
-- Attach row numbers so we can map request N <-> control N <-> src row N
c AS (
  SELECT control_id, row_number() OVER (ORDER BY control_id) AS rn
  FROM ins_controls
),
r AS (
  SELECT request_id, row_number() OVER (ORDER BY request_id) AS rn
  FROM ins_requests
),
s AS (
  SELECT
    row_number() OVER (ORDER BY ref) AS rn,
    ref, vgcpid, title, notes, control_owner, control_sme, escalation,
    assigned_tester_name,
    dat_status, dat_step,
    oet_status, oet_step,
    request_status,
    date_started, due_date, eta, date_completed
  FROM src
)
-- ----------------------------
-- TESTS: two per row (DAT + OET)
-- ----------------------------
INSERT INTO tests (
  request_id, control_id, test_type, assigned_tester_id,
  description, start_date, estimated_date, complete_date,
  in_progress_step, status
)
SELECT
  r.request_id,
  c.control_id,
  t.track::test_type,
  (SELECT user_id FROM users u
   WHERE lower(u.display_name) = lower(s.assigned_tester_name)
   LIMIT 1) AS assigned_tester_id,
  format('%s test for %s', t.track, s.vgcpid) AS description,
  s.date_started::date,
  s.eta::date,
  s.date_completed::date,
  CASE 
    WHEN t.track='DAT' THEN 
      CASE s.dat_step
        WHEN 'Testing Ready' THEN 'TESTING_READY'::test_progress_step
        WHEN 'Walkthrough Scheduled' THEN 'WALKTHROUGH_SCHEDULED'::test_progress_step
        WHEN 'Testing In Progress' THEN 'TESTING_IN_PROGRESS'::test_progress_step
        WHEN 'Testing Completed' THEN 'COMPLETED'::test_progress_step
        WHEN 'Testing Blocked' THEN 'TESTING_BLOCKED'::test_progress_step
        WHEN 'Testing Canceled' THEN 'TESTING_CANCELED'::test_progress_step
        WHEN 'Addressing Comments' THEN 'ADDRESSING_COMMENTS'::test_progress_step
        WHEN 'Walkthrough Completed' THEN 'COMPLETED'::test_progress_step
        ELSE NULL
      END
    ELSE 
      CASE s.oet_step
        WHEN 'Testing Ready' THEN 'TESTING_READY'::test_progress_step
        WHEN 'Walkthrough Scheduled' THEN 'WALKTHROUGH_SCHEDULED'::test_progress_step
        WHEN 'Testing In Progress' THEN 'TESTING_IN_PROGRESS'::test_progress_step
        WHEN 'Testing Completed' THEN 'COMPLETED'::test_progress_step
        WHEN 'Testing Blocked' THEN 'TESTING_BLOCKED'::test_progress_step
        WHEN 'Testing Canceled' THEN 'TESTING_CANCELED'::test_progress_step
        WHEN 'Addressing Comments' THEN 'ADDRESSING_COMMENTS'::test_progress_step
        WHEN 'Walkthrough Completed' THEN 'COMPLETED'::test_progress_step
        ELSE NULL
      END
  END AS in_progress_step,
  CASE WHEN t.track='DAT' THEN s.dat_status::test_status ELSE s.oet_status::test_status END AS status
FROM s
JOIN c ON c.rn = s.rn
JOIN r ON r.rn = s.rn
CROSS JOIN (VALUES ('DAT'), ('OET')) AS t(track);

-- ----------------------------
-- COMMENTS: one request-level comment per row (tracker notes)
-- ----------------------------
WITH 
c AS (
  SELECT control_id, description, row_number() OVER (ORDER BY control_id) AS rn
  FROM controls
),
r AS (
  SELECT request_id, row_number() OVER (ORDER BY request_id) AS rn
  FROM requests
)
INSERT INTO comments (author_user_id, request_id, test_id, comment_text)
SELECT
  (SELECT user_id FROM users WHERE role='MANAGER'::user_role ORDER BY user_id LIMIT 1),
  r.request_id,
  NULL::bigint,
  COALESCE(c.description, '')::text
FROM c
JOIN r ON r.rn = c.rn
WHERE c.description IS NOT NULL AND length(c.description) > 0;

COMMIT;
