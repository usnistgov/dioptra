.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

Summary
-------

Our systems increasingly rely on Machine Learning (ML) algorithms and models to perform essential functions.
As users of these systems, we must implicitly trust the models are working as designed.
Establishing the trustworthiness of an ML model is especially hard because the inner workings are essentially opaque to an outside observer.
Ideally the models we rely on would be transparent, free from bias, explainable, and secure.
Research has shown that ML models are vulnerable to a variety of adversarial attacks that cause them to misbehave in ways that provide benefit to the adversary.
This has sparked a competition between defenses attempting to mitigate attacks and ever novel attacks that defeat the defenses.
This poses a growing challenge for securing ML systems.

In this changing landscape it is extremely difficult to develop a principled approach to evaluating the strengths and weaknesses of defenses.
While much work has been done to evaluate techniques within a narrow range of conditions, there is a challenge in developing more robust metrics that account for the diversity of attacks that might be mounted against it.
Questions of the generalizability of an algorithm across a range of attacks, or the transferability of a technique across models or datasets must naturally consider the full range of possible conditions.

The NCCoE has built an experimentation testbed to begin to address the broader challenge of evaluation for attacks and defenses.
The testbed aims to facilitate security evaluations of ML algorithms under a diverse set of conditions.
To that end, it has a modular design enabling researchers to easily swap in alternative datasets, models, attacks, and defenses.
The result is an ability to advance the metrology needed to ultimately help secure our ML-enabled systems.

Context
-------

While there is a large variety of types of attacks against ML algorithms, NIST Internal Report 8269 identifies three broad categories: Evasion, Poisoning, and Oracle.
In Evasion attacks, an adversary manipulates the test data (sometimes by altering the physical environment) in order to cause the ML model to misbehave.
Poisoning attacks alter the training data used to create or maintain a model with the intention of causing it to learn incorrect associations.
Oracle attacks attempt to "reverse engineer" a model to learn about details of the training set used to create it, or specific model parameters to replicate the model.

.. figure:: /images/overview-image-attack-examples.png

In the case of image classification, attacks can manifest in many different ways ranging from the addition of noise that is difficult for humans to detect in the training or testing images, to the inclusion of colorful "patches" that are noticeable by a human observer but can be printed and placed in the physical environment to alter the images entering the classifier.

There is an equal variety in the types of defenses researchers have developed to mitigate the effectiveness of attacks.
These range from altering the training paradigm for generating models, to techniques that pre-process test data in an attempt to eliminate any carefully crafted alterations added by an adversary.
Just as with attacks, defenses can be deployed at any stage of the ML development pipeline.
The simplified diagrams of the development pipeline below depict some examples.

.. figure:: /images/overview-attack-interfaces.png
   :figwidth: 49%
.. figure:: /images/overview-defense-interfaces.png
   :figwidth: 49%

The sheer variety of attacks and defenses results in a combinatorial explosion of possible combinations of attacks, defenses, model architectures, and datasets.
This creates a challenge for evaluating the effectiveness of defenses against the full array of attacks it may face.
Dioptra, the NCCoE's machine learning security testbed, addresses this challenge by making it easier for researchers to explore the set of possible combinations.

Audience
--------

We envision an audience with a wide variety of familiarity with and expertise in machine learning.
Newcomers to the platform will be able to run the included demonstrations of attacks and defenses even if they have very little programming experience.

The testbed offers new opportunities for analysts in organizations using ML-enabled products.
For example, the inclusion of testing as part of the build pipeline for 1\ :sup:`st` party developers would help promote more robust products.
Similarly, 2\ :sup:`nd` party consumers of such products might leverage the testbed as part of a verification or risk assessment process.
In both cases it allows them to test a product against a range of attacks, thereby helping to understand what types of threats are most harmful.

We also envision it as an asset to ML researchers developing new solutions.
The testbed will allow them to evaluate the security of any new techniques they develop by running them through their paces.
For example, we envision new defenses being tested against a wider array of attacks than is typically found in the literature.
Similarly, it can facilitate "parameter sweeping" to better understand the degree to which small changes in parameters can affect an algorithm.
It also affords an opportunity to replicate and benchmark well-known results from the research literature.
This ability to repeat experiments to reproduce results is critical for creating and validating reliable metrics.

Scope
-----

The testbed is specifically focused on adversarial attacks against the ML algorithms themselves and defensive techniques designed to mitigate the attacks.
In that spirit, the testbed is not originally designed to embed ML algorithms into a larger system context.
For instance, an automated checkout system based on classifying images of products would require additional engineering.
Defenses that could be applied to the surrounding system are currently out of scope.
Similarly, the initial focus has been on image classification algorithms due to the prevalence of available information about attacks and defenses against such algorithms.
There is nothing about the architecture that inherently limits the scope to computer vision, and it would be relatively straightforward to include algorithms using different modalities such as speech recognition or natural language processing.

It comes packaged with about 10 built-in demonstrations of attacks and defenses from the literature combined in various ways.
The attacks include the Fast Gradient Method evasion attack, the Poison Frogs poisoning attack, and a membership inference oracle attack among others.
Defenses include feature squeezing, adversarial training, and jpeg compression among others.
We anticipate this list will grow with time, and we encourage users to contribute back to the project other algorithms as they are developed.

Assumptions / System Requirements
---------------------------------

Most of the built-in demonstrations in the testbed assume the testbed is deployed on Unix-based operating systems (e.g., Linux, MacOS).
Those familiar with the Windows Subsystem for Linux (WSL) should be able to deploy it on Windows, but this mode is not explicitly supported at this time.
Most included demos perform computationally intensive calculations requiring access to significant computational resources such as Graphics Processing Units (GPUs).
The architecture has been tested on a DGX server with 4 GPUs.
The demonstrations also rely on publicly available datasets such as MNIST handwritten digits, ImageNet, and Fruits360 that are not part of the testbed distribution.
The built-in demonstrations assume that relevant datasets have already been obtained and saved in testbed's Data Storage container.

Architecture Overview
---------------------

.. figure:: /images/testbed-architecture.svg

The testbed is built on a microservices architecture.
It is designed to be deployed across several physical machines but is equally deployable on a local laptop.
The distributed deployment allows the core optimization algorithms to reside on machines with GPUs or other high-powered computational resources, while a local deployment will impose strong computational constraints.

The heart of the architecture is the core testbed API that manages requests and responses with a human user via a reverse proxy.
The backend Data Storage component hosts datasets, registered models, and experiment results & metrics.
It also stores the registered plug-ins which are described in more detail below.
As experiment jobs get submitted, the API registers them on the Redis queue which is watched by a worker pool of Docker containers provisioned with all necessary environment dependencies.
These worker containers run the plugins interacting with the MLflow Tracking Service to coordinate job dependencies and record statistics, metrics, and any generated artifacts.
The user may then interact with the MLflow service directly to access a user-friendly dashboard with relevant results, or they may use the API to mediate access.
The architecture is built entirely from open-source resources making it easy for others to extend and improve upon.

.. figure:: /images/experiment-components.svg

As depicted above, the architecture relies on a modular task plugin system to ease the job of programming new combinations of attacks and defenses.
The task plugins perform various basic, low-level functions such as loading models, preparing data, and computing metrics.
They also implement atomic portions of attacks and defenses such as generating adversarial examples or pre-processing images before inference.
Entry points are larger functional units that consist of various ways to wire together registered task plugins.
This enables users of different levels of experience and expertise to interact with the testbed.
We envision four primary user levels.

Level 1—The Newcomer
   These are individuals with little or no hand-on experience with the testbed.
   They will be able to read the documentation and run the provided demos to learn how to use the testbed.
   They will be able to alter the parameters of the provided demos to create slight variants of the existing experiments.
   Their skill set can be wide spectrum.
   They need not be familiar with the technologies the testbed uses, nor do they have to have much experience with scripting or programming.

Level 2—The Analyst
   These are individuals who want to analyze a wider variety of scenarios.
   They will be able to interface with the testbed's RESTful API to create new experiments from existing entry points.
   They will also learn to create custom entry points from the built-in task plugins.
   They must know how to customize the testbed's code templates, thus a basic knowledge of scripting or programming is required.

Level 3—The Researcher
   These are individuals who want to run experiments using novel metrics, algorithms, and analytical techniques.
   They will be able to implement their own "in-house" task plugins and SDK plugins to create novel entry points that rely on custom algorithms.
   They will need to understand the testbed's plugin architecture to extend it with new functionality.
   They therefore require a solid background in scripting or programming.

Level 4—The Developer
   These are individuals that want to expand the testbed's core capabilities by contributing to the distribution.
   They will add new features by implementing built-in task plugins, RESTful API endpoints, SDK modules, and architecture extensions.
   These individuals will have a deep understanding of the how the testbed's architectural and software components work together.
   They will be able to write reusable code and program applications that conform to coding best practices.
