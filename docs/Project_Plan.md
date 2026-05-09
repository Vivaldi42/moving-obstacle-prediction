# Dynamic Obstacle Detection and Prediction

# Project plan

### Author: Vladislav Stefanov

### Fontys University of Applied Sciences

### Eindhoven

## March 16th, 2026

![Point cloud example](./Images/point_cloud.jpeg)




---
# Version History
| Version | Date | Ammendment |
| --- | --- | --- |
| 0.1 | 03.03.2026 | First version ready for review |
| 1.0 | 16.03.2026 | Applying feedback from stakeholders on research questions and timeplan|

<div style="page-break-after: always;"></div>

# 1. Context

The graduation project is conducted within the High Tech Embedded Software (HTES) Research Group at Fontys ICT, part of Fontys University of Applied Sciences in Eindhoven, the Netherlands. HTES focuses on applied research in software methods for smart high-tech embedded systems, particularly in mobile robotics and cyber-physical systems..

Within the research group, multiple mobile robotics projects share a common technical limitation: the absence of a reliable system for tracking and motion prediction of dynamically moving obstacles based on 3D depth perception. Current projects rely on classical perception and filtering methods, while recent developments in AI-based world models have not yet been explored.

This project aims to design and evaluate a modular 3D perception and motion prediction pipeline, while also assessing whether world models offer practical advantages over established classical methods. **By addressing the current limitations, the project seeks to deliver a reusable perception module applicable across multiple HTES robotics platforms, including the Brum used in the Self-Driving Challenge, the Jackal UGV, the Boomba triangular robot platform, and the Avular Origin One.** 

The results should provide a clear, evidence-based conclusion on whether world models represent a promising direction for further research within HTES or whether their practical constraints limit their suitability for mobile robotics applications.

---

# 2. Problem Description

Mobile robotic systems must perceive and interpret dynamic scenes in order to function safely and autonomously. While depth cameras are commonly used for collision prediction, the existing implementations within the HTES research context are limited in dynamic scenes.

The core problem is the absence of an object-centric perception pipeline that can:
1. Detect arbitrarily moving objects using depth data (detection).
2. Maintain consistent identities of those objects over time (tracking).
3. Predict their short-term future motion (prediction).

Without motion prediction, robotic systems react only to the present state of the environment. This reactive behavior limits performance in dynamic scenarios, particularly when obstacles move unpredictably. Higher-level modules such as navigation or path planning require not only knowledge of current obstacle positions, but also reliable short-horizon forecasts of their trajectories.

From a technical perspective, the problem involves several challenges:
- Depth data is noisy and incomplete.
- Object segmentation from point clouds must be robust to clutter and occlusions.
- Multi-object tracking requires reliable data association across frames.
- Motion prediction must account for uncertainty and changing motion patterns.
- The system must remain computationally feasible for real-time operation.

---

# 3. Solution
## 3.1 Overview

The final output of the project is a **modular 3D perception and motion prediction pipeline** that transforms raw depth measurements into:
1. Object-level **detections**
2. Stable object identities over time (multi-object **tracking**)
3. Short-term motion **predictions** with quantified uncertainty

The system must:
- Operate on 3D sensor data (depth data, LiDAR or RGB-D).
- Be modular, such that detection, tracking, and prediction components can be replaced or extended independently.
- Support real-time or near-real-time processing suitable for mobile robotics.
- Produce structured outputs usable by higher-level autonomy modules (e.g., navigation, planning).

A ROS2-based implementation is desirable for integration within HTES robotics projects, but the research and development of the perception pipeline is the primary requirement.

---

## 3.2 Scope

The plan is structured into three phases:

### Phase 1 - Problem Understanding

- Understand robotics perception and analyze perception requirements for mobile robotics.
- Identify limitations of reactive obstacle detection systems.
- Define evaluation metrics.

---

### Phase 2 - State-of-the-Art Review and Experimental Exploration

Topics to research, experiment with and evaluate:

**Sensor Input**
- Depth cameras
- RGB and RGB-D fusion
- LiDAR

**Classical Methods**
- Kalman Filters
- Multi-object tracking
- PCL (Point Cloud Library)
- Open3D
- CUDA acceleration for point cloud processing
- Physics-based game engines for simulation

**State-of-the-Art**
- ZED SDK (highest priority)
- Structured motion representations (SMORE)
- World models for dynamic environments
- NVIDIA Cosmos
- MONet
- Dreamer v3
- DynamicNeRF
- HexPlane
- Autoware
- OpenUSD
- Depth Anything v3
- Isaac Perceptor
- Dino v2
- ConceptGraphs
- ...

**Practical and Educational Resources**
- NVIDIA free online robotics and computer vision courses
- Self-driving challenge documentation
- Robotics perception pipelines

If new relevant approaches are discovered during the project, they may be incorporated following evaluation of their relevance and feasibility.

---

### Phase 3 - Evaluation and Comparison

Evaluation metrics must be explicitly defined and justified. Candidate evaluation criteria:
- Accuracy (task correctness)
- Robustness (performance under harder scenarios)
- Computational efficiency (latency, throughput)
- Stability (consistency)
- Scalability (number of obstacles)

---

### Out-of-Scope (Current Definition)

- Robot motion planning
- Full autonomous system deployment
- Long-term behavior prediction (>5 seconds)
- Large-scale deep learning model training (unless feasible within timeline)

---

## 3.3 Expected Contribution

The project is expected to contribute:
1. A modular perception pipeline for dynamic obstacle tracking and prediction.
2. Empirical comparison of classical methods vs world-model approaches.
3. Experimental validation under controlled conditions.
4. A reusable foundation for HTES mobile robotics projects.

---

# 4. Pre-Conditions

- Working Agile using a Git issue board.
- Using GitLab for version control.
- Using the compute resources of the bigboi PC.
- Using the ISSD for hardware resources (e.g. depth camera).

---

# 5. Research Questions

Main research question:

**How can a modular 3D depth-based perception system reliably detect, track and predict the motion of dynamic obstacles in mobile robotics?**

Sub-questions:
- What are the technical problems with depth-based perception and why are they problems?
- What technologies solving similar problems are available (both classical and state-of-the-art)?
- How to implement one of the available methods and investigate its capabilities?
- What evaluation criteria/metrics are suitable for comparison between different approaches?

---

# 6. Approach

During the internship, I will be using the Agile Scrum approach working with a Git issue board and 2- or 3-week-long sprints. During each sprint, I will perform a research-implement-test cycle for different technologies, sharing the results with the stakeholders. The decision what to work on during a sprint will depend on the stakeholders and will be decided at the beginning of the sprint. We will have weekly meetings with the company mentor and the product owner and another meeting with the first assessor to update them on my progress and ask for feedback.

---

# 7. Learning Outcomes

| Learning outcome | Evidences                                                                                                                                                                  |
| --- | --- |
| **Learning Outcome 1: Professional Duties**<br><br>_You create professional products at bachelor's level within your IT subdomain, in line with the standards and working methods customary in the sector, and you will act accordingly in relevant complex professional situations._                                                                                                      | - project plan<br>- research documentation<br>- experiments and demos of different approaches<br>- comparison between different approaches<br>- prototype of a 3D-depth perception pipeline |
| **Learning Outcome 2: Situation-Orientation**<br><br>_You apply your knowledge and skills in an authentic professional context, where your activities and choices are aligned with the needs, processes and standards of the organisation and lead to demonstrable value for stakeholders._                                                                                                | - feedback from the stakeholders<br>- demos<br>                                                                                                                                             |
| **Learning Outcome 3: Professional Standards**<br><br>_You take responsibility when solving an ICT issue. You define and carry out your research using relevant selected methodologies, and provide advice to your stakeholders even in complex and uncertain contexts. You substantiate and validate future-oriented choices by use of ethical, intercultural and sustainable arguments._ | - research documentation<br>- demos                                                                                                                                                         |
| **Learning Outcome 4: Personal Leadership**<br><br>_You independently formulate goals and actions that demonstrate leadership in your own long term development as an ICT professional. You show that you are capable of carrying out these actions and achieving your goals, adjusting them as necessary._                                                                                | - project plan<br>- Git issue board<br>- feedback from the stakeholders                                                                                                                     |

---

# 8. Time Plan

The internship planning is split in five sprints with a length of three weeks on average, followed by the graduation conference. Additionally, there are four portfolio submissions in total I need to provide evidences for.

| Sprint N              | Duration        |
| --------------------- | --------------- |
| Sprint 1              | Mar 19 - Apr 8  |
| Sprint 2              | Apr 9 - Apr 24  |
| Sprint 3              | May 6 - May 27  |
| Sprint 4              | May 28 - Jun 17 |
| Sprint 5              | Jun 18 - Jul 10 |
| Graduation conference | Jul 13 - Jul 17 |

| Portfolio Submission                                 | Date       |
| ---------------------------------------------------- | ---------- |
| Portfolio snapshot 1 including project plan (week 5) | March 20th |
| Portfolio snapshot for midterm review (week 10)      | April 24th |
| Concept of final portfolio (week 15)                 | June 5th   |
| Final portfolio submission (week 17)                 | June 17th  |

![Timeplan](excel_timeplan.png)


---

# 9. Stakeholders and Communication

| Name                    | Email                        | Role and Responsibilities                          | Availability                                                                          |
| ----------------------- | ---------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Vladislav Stefanov      | v.stefanov@student.fontys.nl | Intern<br><br>Executes and coordinates the project | Every day during the working week                                                     |
| Edwin van den Oetelaart | e.vandenoetelaar@fontys.nl   | Company mentor                                     | Every Wednesday, 15:00-16:00<br><br>Online or in person during the working week       |
| Martin Roa Villescas    | m.roavillescas@fontys.nl     | Product owner                                      | Every Wednesday, 15:00-16:00<br><br>Online during the working week                    |
| Teade Punter            | teade.punter@fontys.nl       | Research chair of HTES                             | Once in several weeks on Wednesday, 15:00-16:00<br><br>Online during the working week |
| Mark Beks               | m.beks@fontys.nl             | First assessor                                     | Every Monday, 13:30-14:00<br><br>Online during the working week                       |
| Ben Schreur             | b.schreur@fontys.nl          | Second assessor                                    | Midterm review, final presentation                                                    |

---

# 10. Risk Management

| Risk Category        | Description                                                                                            | Probability | Impact | Mitigation Strategy                                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------ | ----------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Scope creep          | Expansion into too many advanced methods (e.g., world models, deep learning) exceeding available time. | High        | High   | - Define strict MVP<br>- Frequent feedback sessions with stakeholders<br>- Perform experiments, not only research |
| Technical complexity | Selected approaches (e.g., tracking, prediction models) prove more complex than expected.              | Medium      | High   | - Start with simple baseline models<br>- Incrementally increase complexity                                                               |
| Evaluation ambiguity | Metrics are poorly defined, leading to unclear or non-comparable results.                              | Medium      | High   | - Define evaluation metrics early<br>- Use established benchmarks where possible                                                         |
| Time constraints     | Underestimation of development or experimentation time.                                                | Medium      | High   | - Include buffer time<br>- Work Agile using issues and sprints                                                                           |
| Knowledge gaps       | Insufficient theoretical understanding of filtering, perception, or motion modelling.                  | Medium      | Medium | - Structured literature review<br>- Targeted courses (e.g., NVIDIA robotics/vision) <br>- Experimentation                               |

---

# 11. References

Scrum Guide | Scrum guides. (n.d.). https://scrumguides.org/scrum-guide.html