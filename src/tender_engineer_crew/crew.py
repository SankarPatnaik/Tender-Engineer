#crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List


@CrewBase
class TenderEngineerCrew():
    """TenderEngineerCrew: Automates tender processing from industrial PDFs"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # ---------------- AGENTS ---------------- #

    @agent
    def pdf_reader(self) -> Agent:
        return Agent(
            config=self.agents_config['pdf_reader'],
            verbose=True,
            tools=[FileReadTool(file_path="file_path")]
        )

    @agent
    def tender_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['tender_analyst'],
            verbose=True
        )

    @agent
    def template_mapper(self) -> Agent:
        return Agent(
            config=self.agents_config['template_mapper'],
            verbose=True
        )

    @agent
    def tender_validator(self) -> Agent:
        return Agent(
            config=self.agents_config['tender_validator'],
            verbose=True
        )

    # ---------------- TASKS ---------------- #

    @task
    def extract_pdf_text(self) -> Task:
        return Task(
            config=self.tasks_config['extract_pdf_text']
        )

    @task
    def analyze_tender_content(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_tender_content']
        )

    @task
    def map_to_template(self) -> Task:
        return Task(
            config=self.tasks_config['map_to_template'],
            output_file='output/tender_data.json'
        )

    @task
    def validate_tender_json(self) -> Task:
        return Task(
            config=self.tasks_config['validate_tender_json'],
            output_file='output/tender_validation.json'
        )

    # ---------------- CREW ---------------- #

    @crew
    def crew(self) -> Crew:
        """Creates the Tender Engineer Crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
