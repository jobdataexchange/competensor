# Competensor overview
Competensor is an open source efficient library for cross-level semantic matching of unstructured text to structured framework descriptions. It was developed with funding from the US Chamber of Commerce Foundation to power automatic competency translation from job postings to selected rows from occupational and industrial competency frameworks. It has been designed to process 50+ job postings a second across a wide variety of competency frameworks. Competensor leverages Tensorflow, Auto-Sklearn, Pandas, and Numpy. Competensor was used in the JDX pilot to test an example tool for parsing competencies and skills from job descriptions or postings.

# What is this
This is reference quality code. If you would like help getting this running please reach out to engineering@brighthive.io or open an issue here on github.

# JDX
This was developed and used in conjunction with JDX API which is a JobSchema+ creation API. Parts of competensor are currently tightly coupled and depend on JDX API to be running and making calls. https://github.com/jobdataexchange/jdx-api

# Running competensor
Currently competensor usage is coupled with JDX-API. Running competensor without running JDX-API will cause competensor to fail to start because it relies on JDX-API’s database to be running.

Competensor can be easily decoupled from JDX-API to suite your needs. Don’t hesitate to contact us (engineering@brighthive.io) for help.

Currently JDX-API is not yet open source but we are working on doing so.

First `git clone` competensor to your local computer.
`docker-compose up`

Again, running these commands will start competensor but it will fail. In order to prevent it from failing first

`git clone` JDX-API
`docker-compose up`

## Running on older versions of Docker
Docker has two flavors, virtual machine (VMs) versions and native versions. Older versions run VMs while the newer version run natively. VM versions of docker may have a set memory limit that is too low for competensor and cause a bash error `137` (out of memory).

If you encounter this simply set your memory limit higher. Mac Docker was limiting at 2 GB by default and by moving it up to 4 GBs it resolved the 137 error for us.

### Setting Docker Memory Limit on Mac
Go to Docker Machine Icon -> Preferences -> Advanced, slide memory from 2GiB to 4Gib

# Notes
Competensor uses a model, `linear_5_19.joblib`, to predict textual similarity in an efficient manner. This model was created using `auto-sklearn` and course description data from the [American Council on Education (ACE)](www.acenet.edu). ACE sentence level course skills and Li et al [1] derived similarity measures were used to create initial training data for learning an efficient model for semantic similarity based on corpus statistics (WordNet node statistics) and lexical taxonomy (WordNet graph statistics). To enable greater runtime efficiency, sentences are converted to vector form using Google’s Universal Sentence Encoder [2] to provide an efficient unit of analysis from which to re-learn Li graph derived similarity measures as well as enable efficient inner product calculations to enable efficient multi-stage semantic similarity computation. Exploratory data analyses were performed on the results along with information theoretic statistics to determine the best cut off for BrightHive’s then current needs. This model is publically available on Amazon S3; reach out to engineering@brighthive.io to find out more or consider creating your own model and sharing it via an open source license.

[1] Li, et al, “Sentence Similarity Based on Semantic Nets and Corpus Statistics,” August 2006, IEEE Transactions on Knowledge and Data Engineering 18(8):1138-1150. DOI: 10.1109/TKDE.2006.130. Accessed on 9/18/2019 from: https://www.researchgate.net/publication/232645326_Sentence_Similarity_Based_on_Semantic_Nets_and_Corpus_Statistics/

[2] Cer, et al, “Universal Sentence Encoder”. arXiv. May 2018. Accessed on 9/18/2019 from:  https://arxiv.org/abs/1803.11175

# Making your own model
The ./speedup folder contains code that was used to create the core Comptensor model, `lienar_5_19.joblib`. However this code is in pre-alpha state and is only released as a starting point. The `./speedup/data/` folder contains ACE course descriptions labeled via Li et al semantic similarity measure in [Feather format](https://wesmckinney.com/blog/feather-arrow-future/) as training data for `./speedup/train_regressor.py`.

If you want to make your own model use the `speedup` section of code, modify it for your purposes and train on self provided training data. Previously a MIT licensed fork of the [skills-ml semantic similarity](https://github.com/workforce-data-initiative/skills-ml) module was used but the (Sematch)[https://github.com/gsi-upm/sematch] also provides an efficient implementation of Li’s semantic similarity; you will have to use that. Overall, this folder is considered a research product that will require extra work for your use.

