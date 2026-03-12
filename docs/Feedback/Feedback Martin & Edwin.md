## 11.03.2026
- Project organization: Use an issue board (in this order):
	- product goal
	- backlog of issues (user stories). Each issue has a definition of done (document, paragraph in a doc, demo, prototype,... a concrete deliverable). Issue examples: investigate XYZ, make a prototype of XYZ, define metrics,...
	- sprint goal
	- issues in the current sprint
- Write down a table of sprints (3 weeks per sprint). At the end of every sprint - review and planning -> define a sprint goal.
- Update the repo readme.
- If you can't deliver an issue on time report early during the sprint.
- I can be in Bulgaria for my cousin's wedding (Apr. 25 - May 5th).

- Don't spend time on researching thermal cameras.
- Isaac Perceptor may be nice to research. Check is ZED SDK compatible with it.
- Dino v2 may also be nice to research. Compare it with DA3.
- Initially the comparisons between different methods can be done with synthetic data.
- If the goal is to track moving objects you can track:
	- trajectory of objects (more valuable, more difficult)
	- end point after N s
- Think how useful is XYZ for the self-driving challenge. E.g. using multiple cameras (for 360° sim) can be fun, but not valuable at this stage.
- Derivation of motion -> next position.
- **1st try to make it work using 1 zed camera.**
---
## 04.03.2026
Went through the project plan and discussed it.

- Change the subquestions and time plan in the project plan.

- Subquestions:
	- Answering them means answering the main research question.
	- Refactor them to be more specific and answer all aspects of the research (e.g., how to get an AI model up and running).

- The time plan looks waterfall, make it in a way to showcase numerous research-prototype-validate cycles.
- In general the project is split in 2 big phases:
	  1. Exploration: many research-prototype-validate cycles.
	  2. Implement 1-2 approaches on a physical robot.
- Take several issues per sprint. If stuck on one, use the momentum to work on another. Research as much as possible, don't get blocked.
- Motivate the order of researching different methods. E.g., two completely different approaches in parallel.

- What to work on in the coming 2 weeks?
	- ZED SDK
	- Depth Anything v3
	- Self-driving challenge docs
	- Overview of perception pipelines (incl. Nvidia free online courses) 
- Next meeting: Wed 14:00-15:00
- Arrange a meeting with Teade in the coming 2-3 weeks.

- There are solutions and research papers on the topic of occlusions.
- Reliability is a suitable metric: confidence levels as a % (e.g., 85% this to be a dog, 80% to be a cat).
- This seems promising, nice to try it out (the new NERF Nvidia model that Edwin sent you): https://www.youtube.com/watch?v=WNsSzX0L4Es
- Be careful with sudo on the big PC.
---
## 26.02.2026 (Martin only)
- What are different methods of solving the problem? You need to understand at high level what are they and how do they compare. (Probably the trade off between them is speed vs accuracy.)
- Choose metrics in the project plan.
- Project management environment:
	- Create a git repo and share it with Martin and Edwin. 
	- Use git board with sprints, milestones, backlog/user stories.
	- Teams group chat with Edwin, Martin and Teade.
- Using Obsidian is fine for docs.
- Martin wants to be have time to prepare for sprint review and planning meetings.
- Watch Nvidia courses.
- Write down the newly gained knowledge in your own words (the same way you did it for robotics in S6).
- Is hardware known? Is it any Nvidia HW or bigboi only. Edwin told me to 1st use the bigboi and later during the project to think about something else.
- Research depth camera vs Lidar pros and cons.
---
## 11.02.2026

- Weekly meetings: Wed 3-4 PM

- Research:
	- Depth cameras vs Lidar (maybe not a good idea).
	- Game engine vs world model. Try to run Nvidia Cosmos on bigboi.
	- Stereolabs ZED camera.
	- Is grouping on a class of objects enough.
	- Other methods to solve the problem (literature review).
	- Is it better to use 3D or both 3D+RDB.

- Project organization:
	- Do small steps and iterate quickly. Break and move on quickly.
	-  Work Agile and plan work in sprints.
	- Define measurable and testable research questions. Answer a research question per sprint.
	- Think what way of working will bring max value for stakeholders.

- Write down strong motivation for the project in the project plan.

- For now work on bigboi (set up a VPN). Later you can transfer to Jetson or other edge device.
- For now focus on: 3D point clouds and 3D technologies; is identifying and detecting objects separate steps?

- End product as a ROS2 node is Nice to have. If you don't reach that far, someone else may wrap it up as a ROS2 node.
