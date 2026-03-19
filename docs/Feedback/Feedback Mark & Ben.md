# 16.03.2026
First company visit with Mark and Edwin - narrowing down the scope:
- In the coming weeks focus on ZED SDK and its API: body tracking, positional tracking,... Probably the features of detection and tracking of humans can be fully reused from ZED SDK. After that you can focus on prediction of humans.
- Make several input datasets (pictures, videos) with a ZED camera and use them as a repeatable and controlled experiment for comparing different approaches.
- Research the classic methods a little bit, eg how classic vision works for following a moving ball.
- Lidar is probably out of scope.
- 
## 09.03.2026
Graduation Table Meeting 1: Planning and project organization
- You need to define measurable and testable acceptance criteria for the project to pass.
- Research horizontal and vertical slices as Agile approaches.
- An idea may be to try to make a environment simulation with multiple cameras (to make it 360 degrees or at least to have a wider field of view than just 1 camera).
- Talk with Edwin and Martin about setting up a controlled and repeatable experiment for the different approaches. Useful as a demo at the final presentation.
- For the next graduation table ask for feedback, have questions prepared (eg is my approach correct, what could be improved), show a demo, explain how you answered some of the research questions.
 
## 23.02.2026
- When presenting examples of point clouds generated using Depth Anything v3. the feedback was that it is nice because only 1 camera is needed to create a 3D map of the environment but it may be tricky and risky, for now it is unclear how deterministic the model is. Still, it is valuable to include it in the research.  
- ZED SDK (provided by the camera supplier) is probably more reliable than Depth Anything.  
- If available, check out Lidar or Lidar+RGB images.  
- Take a look at the Nvidia free online courses (e.g., autonomous robots, CUDA,...).

## 10.02.2026 - Intro
Went through the project proposal and discussed it.  
  
- Research:
	- Kalman filters (make a lot of sense for this project).
	- what is better: depth camera or Lidar sensor (maybe velocity can be estimated from Doppler effect).  
	- what is better: physics-based game engine (proven technology) or world models (new and less certain technology; maybe physics will be unrealistic and artifacts will exist).  
	- should the final product be a ROS2 program/node or something else.  

- Experiments:
	- Use real cameras, real input data in controlled environment. Do not use synthetic data only.  
	- Actual measurements will be needed.  
	- Simple high-school experiment can be developed - a ball falling down a ramp being tracked by a camera. Control camera (actual measurements) and test cameras (predictions) can be used for comparison.  

- Timeline:
	- Final portfolio delivery: Week 15.  
	- Assessment (do extra tasks if required by assessors): Week 16-17.
	- Official end of internship: July 10.  
	- Graduation ceremony: Week 21.
	- Weekly meetings: 13:30-14:00 on Mondays.

- Portfolio:
	- LO1 Professional Duties: the bulk of the work. More evidences expected compared to the other learning outcomes.  
	- Portfolio needs to be structured and readable. Make references between documents or different sections of the same document.  
	- Portfolio logical flow: analysis -> advice -> design -> implementation -> manage and control.
	- 1st portfolio submission: project plan made specifically for the project, not general key points valid for any project. Project plan will deviate from the actual project inevitably.