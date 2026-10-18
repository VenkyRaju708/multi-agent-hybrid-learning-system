"""Builds eval/questions.csv: 100 labelled questions (40 document, 40 topic, 20 mixed).

Document and mixed questions are written from the two JISEM 2023 papers by
V. Viswanathan (open access, CC BY 4.0, also on Zenodo records 19293231 and
17676883). Labels were fixed before any run, as the eval README requires.
"""
import csv
from pathlib import Path

P1 = "AI-Augmented_Decision_Intelligence_JISEM_2023.pdf"   # JISEM 8(2) 2023
P2 = "Generative_AI_Workforce_Planning_JISEM_2023.pdf"     # JISEM 8(4) 2023

DOC1 = [
    ("How many samples were in the synthetic dataset used in this paper?", "220 samples"),
    ("What percentage of the samples were classified as Decision Intelligence users?", "29%"),
    ("What was the mean Performance Metric of DI users compared with non-users?", "users M=82.5;non-users M=64.3"),
    ("Which software platform was used to run the statistical analyses?", "Jamovi 2.x"),
    ("What significance threshold did the study set?", "p < 0.005"),
    ("Which databases were searched for the literature review?", "IEEE Xplore;Scopus;SpringerLink"),
    ("Which reporting standard guided the systematic literature review?", "PRISMA"),
    ("List the variables included in the synthetic dataset.", "Experience Years 1-20;Role Level Junior to Manager;Training Hours;AI_Skill_Score 0-100;Decision_Intelligence_Adoption 0/1;PerformanceMetric"),
    ("What coefficient did DI adoption have in the multiple regression, and was it significant?", "beta=0.44;p<0.001"),
    ("What adjusted R-squared did the regression model report?", "adjusted R2=0.71"),
    ("According to Table 1, which role level had the highest mean performance, and what was it?", "Manager;mean 78.3"),
    ("How many Junior employees were in the dataset?", "68"),
    ("What t-statistic and degrees of freedom does Table 2 report for the Performance Metric?", "t=-14.15;df=218;p<.001"),
    ("What p-values did Levene's test give for AI Skill Score and Performance Metric?", "AI Skill Score p=0.298;Performance Metric p=0.127;equal variances assumed"),
    ("What did the logistic regression show about who adopts DI tools?", "employees with higher AI skills;and more training hours;were more likely to adopt DI"),
    ("Which authors does the paper credit with the concept of collaborative intelligence?", "Daugherty and Wilson [14]"),
    ("What future research directions does the paper list?", "longitudinal studies linking DI to ROI and retention;cross-industry comparison of DI frameworks;explainable AI;ethical standards and governance for human-in-the-loop DI"),
    ("What affiliations does the author list on the paper?", "PhD Scholar Annamalai University;IT Project Manager Novalink Solutions LLC USA"),
    ("What does the paper conclude about data maturity and DI success?", "well-organized integrated high-quality data systems use DI more fully;poor or fragmented data limits performance gains"),
    ("What model specification was used for the multiple regression?", "PerformanceMetric ~ DI adoption + skill + experience"),
]

DOC2 = [
    ("How many enterprises were included in the study's sample?", "120 enterprises"),
    ("Which sectors were the enterprises drawn from?", "technology;finance;healthcare;manufacturing"),
    ("What sampling method was used to select the enterprises?", "purposive sampling"),
    ("Who completed the structured questionnaires?", "managers and HR personnel;responsible for workforce planning and operational decisions"),
    ("What was the mean AI Usage Level across enterprises?", "58.2"),
    ("What was the mean Workforce Productivity?", "61.4"),
    ("What were the mean Decision Efficiency and mean Employee Satisfaction?", "Decision Efficiency 48.1;Employee Satisfaction 49.1"),
    ("What range of AI Usage Level values was observed?", "minimum 20.4;maximum 99.0"),
    ("What was the highest Workforce Productivity value recorded?", "122.5"),
    ("How does the paper describe the shape of the AI usage distribution in the histogram?", "roughly bimodal;clusters at moderate and high adoption"),
    ("What kind of plot is Figure 3 and what does it combine?", "violin plot;combines boxplot and kernel density"),
    ("What research design did the study use?", "quantitative;cross-sectional;descriptive-correlational"),
    ("How was AI Usage Level measured?", "0-100 scale;extent of generative AI integration;automation, predictive analytics and AI-assisted decision-making"),
    ("How was Decision Efficiency assessed?", "speed and accuracy of decisions;facilitated by AI tools"),
    ("What range did the standard deviations of the key variables fall in?", "20.3 to 26.3"),
    ("What productivity gains does the paper attribute to Brynjolfsson et al.?", "up to 15%;more pronounced among knowledge workers"),
    ("Which barriers to AI adoption does the paper mention?", "insufficient digital infrastructure;limited workforce training;high implementation costs"),
    ("What future work does the paper propose?", "longitudinal analyses;causal/predictive modelling;sector-specific variation;role of training, change management and culture;ethical and social implications"),
    ("What were the four lowest AI Usage Level values in Table 2?", "20.4;21.6;22.0;22.5"),
    ("When was the paper received and accepted?", "received 04 Oct 2023;accepted 20 Dec 2023"),
]

TOPIC = [
    ("What is the difference between supervised and unsupervised learning?", "supervised uses labelled data;unsupervised finds structure without labels"),
    ("What is overfitting and how can it be prevented?", "model fits noise in training data;poor generalisation;regularisation, more data, early stopping or cross-validation"),
    ("What is the difference between precision and recall?", "precision = TP/(TP+FP);recall = TP/(TP+FN)"),
    ("How does gradient descent work?", "iteratively updates parameters;opposite the gradient of the loss;learning rate sets step size"),
    ("What is the main idea of the transformer architecture?", "self-attention instead of recurrence;processes tokens in parallel;encoder/decoder stacks"),
    ("What does self-attention compute?", "weights each token against every other token;queries, keys and values"),
    ("What is retrieval-augmented generation?", "retrieve relevant passages;add them to the prompt;generate a grounded answer"),
    ("What are word embeddings?", "dense vectors representing words;similar meanings lie close together"),
    ("What is cosine similarity?", "cosine of the angle between two vectors;dot product divided by product of norms;range -1 to 1"),
    ("What is tokenization in large language models?", "splitting text into tokens or subwords;tokens map to IDs the model processes"),
    ("What are convolutional neural networks mainly used for?", "grid-like data such as images;convolutional filters learn local features"),
    ("What is the bias-variance tradeoff?", "bias = error from simplifying assumptions;variance = sensitivity to training data;balance to minimise total error"),
    ("How does k-means clustering work?", "choose k centroids;assign points to nearest centroid;recompute centroids until stable"),
    ("What is cross-validation used for?", "estimate performance on unseen data;split data into folds;train and test on different folds"),
    ("What does dropout do in a neural network?", "randomly disables units during training;reduces overfitting"),
    ("What is the basic idea of reinforcement learning?", "agent acts in an environment;receives rewards;learns a policy maximising cumulative reward"),
    ("How do artificial intelligence, machine learning and deep learning differ?", "AI is the broad field;ML learns from data;deep learning uses multi-layer neural networks"),
    ("What is an API?", "application programming interface;defined way for software components to communicate"),
    ("What is the difference between SQL and NoSQL databases?", "SQL relational with fixed schema;NoSQL flexible schemas such as document or key-value"),
    ("What do IaaS, PaaS and SaaS mean in cloud computing?", "infrastructure as a service;platform as a service;software as a service"),
    ("What does Big-O notation describe?", "growth of an algorithm's time or space with input size;upper bound"),
    ("How does binary search work?", "sorted array;compare with middle element;halve the search range;O(log n)"),
    ("What is the role of TCP in networking?", "reliable ordered delivery;connection-oriented;retransmission and flow control"),
    ("How does photosynthesis work?", "plants convert light, water and CO2;into glucose and oxygen;chlorophyll in chloroplasts"),
    ("What does Newton's second law state?", "F = m a;force equals mass times acceleration"),
    ("Why does Earth have seasons?", "axial tilt of about 23.5 degrees;changes angle and duration of sunlight through the year"),
    ("What is inflation?", "general rise in prices over time;falling purchasing power of money"),
    ("How do supply and demand set prices?", "price rises when demand exceeds supply;equilibrium where supply equals demand"),
    ("What is DNA?", "molecule carrying genetic instructions;double helix;bases A, T, C, G"),
    ("What does the Pythagorean theorem state?", "a^2 + b^2 = c^2;right triangle;c is the hypotenuse"),
    ("What is the GDPR?", "EU General Data Protection Regulation;rules on personal data processing and individuals' rights"),
    ("What is hallucination in large language models?", "fluent but false or unsupported output;not grounded in facts or sources"),
    ("What is the difference between fine-tuning and prompt engineering?", "fine-tuning updates model weights on new data;prompt engineering changes the input only"),
    ("What is automatic speech recognition?", "converts spoken audio to text;acoustic and language models"),
    ("What is text-to-speech synthesis?", "converts text into spoken audio;synthetic voice"),
    ("What is the Turing test?", "test of machine intelligence proposed by Alan Turing;judge cannot tell machine from human in conversation"),
    ("How does a decision tree classifier make predictions?", "splits data on feature thresholds;follows branches to a leaf label"),
    ("What is a confusion matrix?", "table of predicted vs actual classes;true/false positives and negatives"),
    ("What is transfer learning?", "reuse a model trained on one task;adapt it to a related task with less data"),
    ("What is federated learning?", "train across many devices or sites;data stays local;only model updates are shared"),
]

MIXED1 = [
    ("This paper sets its significance threshold at p < 0.005. Explain what a p-value means and how this threshold compares with the common 0.05.", "paper uses p < 0.005;p-value = probability of data this extreme if the null is true;0.005 is ten times stricter than 0.05"),
    ("The paper uses a synthetic dataset of 220 samples. What are the general limitations of synthetic data for drawing real-world conclusions?", "paper: synthetic dataset, 220 samples;synthetic data may not reflect real distributions;findings illustrate the method rather than prove real effects"),
    ("Explain what Levene's test checks, and interpret the Levene results this paper reports.", "Levene's test checks equality of variances;paper: p=0.298 and p=0.127;p > 0.05 so equal variances assumed"),
    ("The paper reports an adjusted R-squared for its regression. What does adjusted R-squared measure and what does this paper's value suggest?", "paper: adjusted R2=0.71;share of variance explained, penalised for number of predictors;0.71 = about 71% explained"),
    ("The paper says its review followed PRISMA. What is PRISMA and what are its main steps?", "paper used PRISMA with IEEE Xplore, Scopus, SpringerLink;PRISMA = reporting guideline for systematic reviews;identification, screening, eligibility, inclusion"),
    ("The paper's t-test reports 218 degrees of freedom. Explain how degrees of freedom are calculated for an independent-samples t-test and check this against the sample size.", "paper: df=218, N=220;df = n1 + n2 - 2;220 - 2 = 218"),
    ("How does Decision Intelligence as described in this paper differ from traditional business intelligence?", "paper: DI combines AI, analytics and decision theory, focuses on decision impact, human-in-the-loop;BI generally reports and describes past data"),
    ("The paper uses Q-Q plots to check its models. What does a Q-Q plot show in general, and what does the paper conclude from its plots?", "Q-Q plot compares sample quantiles with theoretical normal quantiles;points on the line mean approximate normality;paper: near-linear, approximately normal residuals"),
    ("Explain human-in-the-loop design in machine learning and how this paper relates it to Decision Intelligence.", "HITL = humans review or guide model decisions;paper: DI integrates AI with HITL design;future work on governance for human-in-the-loop DI"),
    ("The paper used logistic regression for DI adoption. Why is logistic rather than linear regression used for that kind of outcome?", "paper: DI adoption is 0/1;logistic regression models probability of a binary outcome;linear regression can predict outside 0-1"),
]

MIXED2 = [
    ("This study selected its enterprises by purposive sampling. What is purposive sampling and what is its main limitation compared with random sampling?", "paper: 120 enterprises, purposive sampling;researcher selects cases deliberately;limits generalisability and adds selection bias"),
    ("The study uses a cross-sectional design. Why can a cross-sectional design not establish causation?", "paper: quantitative cross-sectional design;data at a single point in time;cannot show temporal order or rule out confounders"),
    ("The paper presents a violin plot. How does a violin plot differ from a box plot?", "paper Figure 3 is a violin plot;box plot shows median and quartiles;violin adds kernel density showing distribution shape"),
    ("The paper describes the AI usage distribution as roughly bimodal. What does bimodal mean, and why can the mean be misleading for such data?", "paper: bimodal, moderate and high clusters, mean 58.2;bimodal = two peaks;mean may fall between peaks where few cases lie"),
    ("Using the mean and standard deviation the paper reports for AI Usage Level, calculate the coefficient of variation and interpret it.", "paper: mean 58.2, SD 23.8;CV = SD/mean = about 40.9%;relatively high variability"),
    ("The paper cites Brynjolfsson et al. on productivity. What does wider research generally say about how generative AI productivity gains differ between less and more experienced workers?", "paper: gains up to 15%, larger for knowledge workers;Brynjolfsson, Li and Raymond (2023) found largest gains for novice and less-skilled workers"),
    ("The paper's highest Workforce Productivity value is 122.5 although other measures run roughly from 0 to 100. What does this suggest about the measurement scale and possible outliers?", "paper: max productivity 122.5;index not bounded at 100;check scale definition and outliers"),
    ("Employee satisfaction in this study was self-reported. What biases affect self-reported survey measures?", "paper: self-reported survey items;social desirability bias;common-method and recall bias"),
    ("The paper assesses Decision Efficiency by the speed and accuracy of decisions. How else do organizations commonly measure decision quality?", "paper: speed and accuracy facilitated by AI tools;other measures: outcomes against targets, forecast error, decision cycle time, cost of errors"),
    ("What challenges to AI adoption does this paper name, and what general practices help organizations address them?", "paper: infrastructure, training, cost, job security and reskilling concerns;general: training programmes, change management, human oversight, phased rollout"),
]


def rows():
    out = []
    for i, (q, ref) in enumerate(DOC1, 1):
        out.append((f"D{i:02d}", q, "document", "document", P1, ref, "JISEM 8(2) 2023"))
    for i, (q, ref) in enumerate(DOC2, 21):
        out.append((f"D{i:02d}", q, "document", "document", P2, ref, "JISEM 8(4) 2023"))
    for i, (q, ref) in enumerate(TOPIC, 1):
        pdf = P1 if i % 2 else P2  # a document is always loaded, so the router is really tested
        out.append((f"T{i:02d}", q, "topic", "topic", pdf, ref, "general knowledge; document loaded but not needed"))
    for i, (q, ref) in enumerate(MIXED1, 1):
        out.append((f"M{i:02d}", q, "mixed", "mixed", P1, ref, "needs the document and general knowledge"))
    for i, (q, ref) in enumerate(MIXED2, 11):
        out.append((f"M{i:02d}", q, "mixed", "mixed", P2, ref, "needs the document and general knowledge"))
    return out


if __name__ == "__main__":
    r = rows()
    assert len(r) == 100, len(r)
    assert sum(x[2] == "document" for x in r) == 40
    assert sum(x[2] == "topic" for x in r) == 40
    assert sum(x[2] == "mixed" for x in r) == 20
    path = Path(__file__).with_name("questions.csv")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "type", "expected_route", "pdf_file", "reference_points", "notes"])
        w.writerows(r)
    print(f"wrote {path} ({len(r)} rows)")
