from langsmith import Client, traceable
from typing_extensions import Annotated, TypedDict

# With langchain we can easily turn any vector store into a retrieval component:
retriever = new_vector_store.similarity_search_with_score(query, k=3)

llm = tipo_llm()


# Add decorator so this function is traced in LangSmith
@traceable()
def rag_bot(question: str) -> dict:
    # langchain Retriever will be automatically traced
    docs = retriever.invoke(question)

    docs_string = " ".join(doc.page_content for doc in docs)

    instructions = f"""
    You are a helpful assistant who is good at analyzing source information and answering questions.
    Use the following source documents to answer the user's questions.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.

    Documents:
    {docs_string}"""

    # langchain ChatModel will be automatically traced
    ai_msg = llm.invoke(
        [
            {"role": "system", "content": instructions},
            {"role": "user", "content": question},
        ],
    )

    return {"answer": ai_msg.content, "documents": docs}


client = Client()


# Create the dataset and examples in LangSmith
dataset_name = "Lilian Weng Blogs Q&A"
if not client.has_dataset(dataset_name=dataset_name):
    dataset = client.create_dataset(dataset_name=dataset_name)
    client.create_examples(
        inputs=[{"question": q} for q, _ in examples],
        outputs=[{"answer": a} for _, a in examples],
        dataset_id=dataset.id,
    )


# Grade output schema
class CorrectnessGrade(TypedDict):
    # Note that the order in the fields are defined is the order in which the model will generate them.
    # It is useful to put explanations before responses because it forces the model to think through
    # its final response before generating it:
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    correct: Annotated[bool, ..., "True if the answer is correct, False otherwise."]


# Grade prompt
correctness_instructions = """You are a teacher grading a quiz. 

You will be given a QUESTION, the GROUND TRUTH (correct) ANSWER, and the STUDENT ANSWER. 

Here is the grade criteria to follow:
(1) Grade the student answers based ONLY on their factual accuracy relative to the ground truth answer. 
(2) Ensure that the student answer does not contain any conflicting statements.
(3) It is OK if the student answer contains more information than the ground truth answer, as long as it is factually accurate relative to the  ground truth answer.

Correctness:
A correctness value of True means that the student's answer meets all of the criteria.
A correctness value of False means that the student's answer does not meet all of the criteria.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""

# Grader LLM
grader_llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(
    CorrectnessGrade, method="json_schema", strict=True
)


def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    """An evaluator for RAG answer accuracy"""
    answers = f"""      QUESTION: {inputs['question']}
GROUND TRUTH ANSWER: {reference_outputs['answer']}
STUDENT ANSWER: {outputs['answer']}"""

    # Run evaluator
    grade = grader_llm.invoke(
        [
            {"role": "system", "content": correctness_instructions},
            {"role": "user", "content": answers},
        ]
    )
    return grade["correct"]


# Grade output schema
class RelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[
        bool, ..., "Provide the score on whether the answer addresses the question"
    ]


# Grade prompt
relevance_instructions = """You are a teacher grading a quiz. 

You will be given a QUESTION and a STUDENT ANSWER. 

Here is the grade criteria to follow:
(1) Ensure the STUDENT ANSWER is concise and relevant to the QUESTION
(2) Ensure the STUDENT ANSWER helps to answer the QUESTION

Relevance:
A relevance value of True means that the student's answer meets all of the criteria.
A relevance value of False means that the student's answer does not meet all of the criteria.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""

# Grader LLM
relevance_llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(
    RelevanceGrade, method="json_schema", strict=True
)


# Evaluator
def relevance(inputs: dict, outputs: dict) -> bool:
    """A simple evaluator for RAG answer helpfulness."""
    answer = f"""      QUESTION: {inputs['question']}
STUDENT ANSWER: {outputs['answer']}"""
    grade = relevance_llm.invoke(
        [
            {"role": "system", "content": relevance_instructions},
            {"role": "user", "content": answer},
        ]
    )
    return grade["relevant"]


# Grade output schema
class GroundedGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    grounded: Annotated[
        bool, ..., "Provide the score on if the answer hallucinates from the documents"
    ]


# Grade prompt
grounded_instructions = """You are a teacher grading a quiz. 

You will be given FACTS and a STUDENT ANSWER. 

Here is the grade criteria to follow:
(1) Ensure the STUDENT ANSWER is grounded in the FACTS. 
(2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

Grounded:
A grounded value of True means that the student's answer meets all of the criteria.
A grounded value of False means that the student's answer does not meet all of the criteria.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""

# Grader LLM
grounded_llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(
    GroundedGrade, method="json_schema", strict=True
)


# Evaluator
def groundedness(inputs: dict, outputs: dict) -> bool:
    """A simple evaluator for RAG answer groundedness."""
    doc_string = "

".join(doc.page_content for doc in outputs["documents"])
    answer = f"""      FACTS: {doc_string}
STUDENT ANSWER: {outputs['answer']}"""
    grade = grounded_llm.invoke(
        [
            {"role": "system", "content": grounded_instructions},
            {"role": "user", "content": answer},
        ]
    )
    return grade["grounded"]


# Grade output schema
class RetrievalRelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[
        bool,
        ...,
        "True if the retrieved documents are relevant to the question, False otherwise",
    ]


# Grade prompt
retrieval_relevance_instructions = """You are a teacher grading a quiz. 

You will be given a QUESTION and a set of FACTS provided by the student. 

Here is the grade criteria to follow:
(1) You goal is to identify FACTS that are completely unrelated to the QUESTION
(2) If the facts contain ANY keywords or semantic meaning related to the question, consider them relevant
(3) It is OK if the facts have SOME information that is unrelated to the question as long as (2) is met

Relevance:
A relevance value of True means that the FACTS contain ANY keywords or semantic meaning related to the QUESTION and are therefore relevant.
A relevance value of False means that the FACTS are completely unrelated to the QUESTION.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""

# Grader LLM
retrieval_relevance_llm = ChatOpenAI(
    model="gpt-4o", temperature=0
).with_structured_output(RetrievalRelevanceGrade, method="json_schema", strict=True)


def retrieval_relevance(inputs: dict, outputs: dict) -> bool:
    """An evaluator for document relevance"""
    doc_string = "

".join(doc.page_content for doc in outputs["documents"])
    answer = f"""      FACTS: {doc_string}
QUESTION: {inputs['question']}"""

    # Run evaluator
    grade = retrieval_relevance_llm.invoke(
        [
            {"role": "system", "content": retrieval_relevance_instructions},
            {"role": "user", "content": answer},
        ]
    )
    return grade["relevant"]


def target(inputs: dict) -> dict:
    return rag_bot(inputs["question"])


experiment_results = client.evaluate(
    target,
    data=dataset_name,
    evaluators=[correctness, groundedness, relevance, retrieval_relevance],
    experiment_prefix="rag-doc-relevance",
    metadata={"version": "LCEL context, gpt-4-0125-preview"},
)

# Explore results locally as a dataframe if you have pandas installed
# experiment_results.to_pandas()