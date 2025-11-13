"""
Evaluation script for Alaska Snow Department Agent.

Evaluates agent performance using the Google Evaluation API.
"""

import pandas as pd
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vertexai
from vertexai.preview.evaluation import EvalTask
from vertexai.generative_models import GenerativeModel, GenerationConfig
from app.config import PROJECT_ID, LOCATION, ADS_SYSTEM_INSTRUCTION


def display_eval_report(report_data):
    """Display evaluation report."""
    name, summary, metrics_table = report_data
    print(f"\n{name}")
    print("-" * 70)
    print("\nSummary Metrics:")
    print(summary)
    print("\nDetailed Metrics:")
    print(metrics_table)


def main():
    """Run evaluation on Alaska Snow Agent."""
    
    # Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel(
        model_name="gemini-2.5-pro",
        system_instruction=ADS_SYSTEM_INSTRUCTION
    )
    
    # Load evaluation dataset
    eval_data = pd.read_csv("eval_dataset.csv")
    print(f"Loaded {len(eval_data)} evaluation examples")
    
    # Define prompt template (simulates the agent's prompting)
    prompt_template = """Answer the user's question about Alaska snow services.

User Question: {instruction}

Provide a helpful, accurate answer."""
    
    # Create evaluation task
    print("\nRunning evaluation with BLEU and ROUGE metrics...")
    eval_task = EvalTask(
        dataset=eval_data,
        metrics=["bleu", "rouge_1", "rouge_l"],
        experiment="alaska-snow-agent-eval"
    )
    
    # Run evaluation
    run_ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    result = eval_task.evaluate(
        model=model,
        prompt_template=prompt_template,
        experiment_run_name=f"agent-eval-{run_ts}"
    )
    
    print("\n✓ Evaluation complete!")
    
    # Display results
    display_eval_report(("Alaska Snow Agent Evaluation", result.summary_metrics, result.metrics_table))
    
    # Summary
    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)
    print(f"Questions evaluated: {len(eval_data)}")
    print(f"BLEU score: {result.summary_metrics.get('bleu/mean', 0):.3f}")
    print(f"ROUGE-1 score: {result.summary_metrics.get('rouge_1/mean', 0):.3f}")
    print(f"ROUGE-L score: {result.summary_metrics.get('rouge_l/mean', 0):.3f}")
    print("="*70)


if __name__ == "__main__":
    main()

