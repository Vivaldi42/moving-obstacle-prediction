# Feedback from Martin (product owner) and Edwin (company mentor)

# 25.03.2026
- SDC Brum: Check Edwin's original design of the Brum and research Zenoh and ZeroMQ.
- Stream live video on both big PC and Jetson. Use different base images for bigboi and Jetson.
- Check if X11 can run on Jetson.
- When doing research (eg on CV, robotics, autnav): 1) take a step back; look at what you need to deliver 2) what level of detail provides enough understanding so I can move forward and solve the problem at hand. Ask yourself what question would you ask an expert related to this topic. To have intuitive understanding is enough for many terms.
- Maybe depth map is enough and point clouds are not needed.
- Research the tradeoff between RDB, RGB-D and point clouds.
- What is the pipeline input -> ? -> depth map.

# 18.03.2026
- Put all issues you think are needed during the project in the backlog. Put subtasks in issues. Make a proposal git board and send it to Martin.
- Use sprints as milestones and write down sprint goals.
- Be unambiguous and concrete in documentation.
- Run ZED body tracking + trajectory. 1st humans then other objects. How to go from humans to arbitrary objects?

- Research what hardware is needed for ZED SDK? 
- Your system must be a reproducible and portable package (can be reused on the big PC, the Jetson,...). Ensure that it can work on different devices. How to measure performance on different HW e.g., FPS?
 
- Issue: Investigate the basics of Docker and implement a Docker machine that runs ZED SDK on big PC. Which base image is best for ZED SDK? Big PC is AMD and Orin is ARM but Docker runs on both. You can arrange a meeting with Martin to help with Docker. dockerhub? VM? container? dev container (don't use this, spend a little time on it)? image? how to access HW from container? install docker, run webserver in Docker. figure out if ZED SDK can run in Docker and did someone use it online.

- New issues:
	- Docker
	- ZED SDK demo
	- Input for repeatable experiments

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
