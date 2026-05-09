# 07.05.2026
- Decided to use RGB-D not point clouds.
- Clarified the design and what the system needs to do.
- Made a python prototype that tracks a moving tennis ball across frames and uses YOLO for object detection.
- Decided that recording other videos is not necessary.

TODO:
- Why it needs to optimize AI models every time when I start the program?
- Add uncertainty of predictions and different potential future trajectories?
- Write a system design document.
- Ensure that the documentation (readme files) aligns with the code functionality.
- Check if the measurements align with the physical world.

# 24.04.2026
- Finished the Docker research document.

# 23.04.2026
- Made a prototype of software system that follows a tennis ball in Python.
 
# 15.04.2026
- Worked on docker for x86 and arm.
	- Set up `3dpipe` with Docker for x86 and Jetson.
	- Switched dev mode to use mounted source code instead of copying files into the image.
	- Added separate Compose services and build folders for x86 and Jetson.
	- Updated the app to stream the ZED left image and show FPS.
	- Jetson build works; remaining issue is Jetson camera runtime access (`nvargus-daemon` / `zed_x_daemon`).
- Had a meeting with Martin and Edwin to share the progress with them.

# 25.03.2026
- I researched Docker more.
- Had a meeting with Edwin and Martin about the progress.
- Had a meeting with O Sigma to talk about Kickoff.

# 24.03.2026
- I talked with Pim about the triangular robot platform.
- I researched Docker and made a Docker container.

# 23.03.2026
- Talked with Edwin about what to focus on. He showed me his online repo of textbooks (https://dmx.e3n.nl/). He advised me to work on Docker.
- With Edwin we moved the bigboi PC to the smart systems lab and set up my working space there.
- I started researching Docker.

# 22.03.2026
- Tried to read the SDC docs but it wasn't very successful (missing docs). Made a system design diagram using ChatGPT that resembles what a real system would look like.

# 21.03.2026
- Researched terms related to CV and robotics.

# 20.03.2026
- Worked on the research docs about intro to robotics.
- Submitted the first version of the portfolio.

# 19.03.2026
- Talked with Edwin and Dancho about creating an advanced Boomba for the educational market.
- Researched robotics and computer vision.
- Made a body detection and tracking demo using the ZED SDK.
- Went to the drones race event.

# 18.03.2026
- Had a meeting with Martin and Edwin.
- Created an issue board for the coming 1/2 sprints.

# 17.03.2026
- Went through ZED SDK tutorials and researched the ZED repo.

# 16.03.2026
- Finished the first version of the project plan incl. feedback from Martin and Mark.
- Had the 1st company visit with Mark and Edwin.
- Had a meeting with Edwin and Teade to discuss my project.

# 13.03.2026
- Tested tailscale communication between my pc and the bigboi.
- Configured remote desktop communication between my pc and the bigboi.
- Talked with Jan about potential business opportunities in mobile robotics and about working space.

# 12.03.2026
- Git repo set up, Codex set up.
- Experimented with the ZED SDK.

# 11.03.2026
- Had a weekly meeting with Edwin and Martin.
- Experimented with the ZED SDK.

# 10.03.2026
- Finally set up the ZED SDK (by installing it again).
- Talked with Edwin about in-memory computing and the possibility to participate in the KickOff pre-accelerator.

# 09.03.2026
- Participated in the 1st graduation table meeting.
## 08.03.2026
- Finished the NVIDIA free online course "A Beginner's Guide to Autonomous Robots"

## 07.03.2026
- Continued further with the NVIDIA free online course "A Beginner's Guide to Autonomous Robots"

## 06.03.2026
- ZED SDK configuration
	- Finally fixed the ZED SDK configuration (fixed problems with the right versions of CUDA, TensorRT, OpenGL (switched from `llvmpipe` to `NVIDIA` renderer). Remaining Issue `ZED_Diagnostic` tool crashes with segmentation fault.  Not critical:  
		- `ZED_Depth_Viewer` works  
		- Python SDK camera open test works  
	- Final Status: ZED SDK is configured and ready to use.

## 05.03.2026

## 04.03.2026
- Had a meeting with Martin and Edwin to show them the project plan. They gave me feedback what needs to be changed and we discussed what to work on in the coming two sprints.
- I wrote down the feedback they gave me.
 
## 03.03.2026
- Finished the project plan and sent it for review to Edwin, Martin and Mark.

## 02.03.2026

## 01.03.2026
- Worked on the project plan.
 
## 28.02.2026
- 

## 27.02.2026
- 

## 26.02.2026
- 

## 16.02.2026
- Found educational courses by Nvidia

## 15.02.2026
- Researched 3D point clouds, object detection and recognition, technologies developed by Nvidia
- Chat with Edwin: sent him the videos of DA3, he said that we can make a demo video of the whole floor at TQ 5.2; DA3 can work with video as input
- Researched the ZED SDK and found how many functionalities are already implemented

## 13.02.2026
- Prepared for a meeting with Bart - The Gate Insitute
- A meeting with Bart - The Gate Institute: showed him a technical mini canvas. He said that 1. What and 3. Leap fordward need to be altered slightly but in general it's good. The next step is to perform market research
- Jan shared with me his attempt to start a company in 2008-2009. He showed me his presentation and gave me very valuable information about his experience
- Learnt about people vibe coding entire apps in just a weekend and the incredible speed of tech innovation
- Learnt about Nvidia Earth-2 and was amazed by the exponential growth of technology

## 12.02.2026
- Update session meeting: intro to lectoraat interns at TQ
- Installed DA3, run it and generated a point cloud of some objects and the room. A very nice achievement!

## 11.02.2026
- Prepared for the first meeting with Edwin and Martin
- Had the first meeting with Edwin and Martin
- Researched what are point clouds and found Depth Anything v3 (DA3)
- Showed DA3 to Edwin and he gave me a task to run it on bigboipc and make a point cloud of the the room
- Went to Tony's and Pom with Edwin and discussed business topics, then I helped him to run the printer at Pom

## 10.02.2026
- Had a meeting with Mark and dicussed the project
- Wrote the notes from the meeting with Mark in Feedpulse
- Tried to set up Nvidia Cosmos
- Attended IXD update meeting where Iman presented the progress on his research
- Attended a KickOff Ehv event with the Picnic CTO and got in touch with him

## 09.02.2026
- Set up Firefox as the default browser
- Attended Internship Kick-off with Pim
- Contacted Mark Beks (1st assessor) and arranged an intro meeting with him
- Arranged an intro meeting with Edwin and Martin
- Tried to finish the configuration of Nvidia Cosmos I started last week
