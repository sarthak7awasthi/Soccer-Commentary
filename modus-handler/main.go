package main

import (
 
    "strings"

    "github.com/hypermodeinc/modus/sdk/go/pkg/models"
    "github.com/hypermodeinc/modus/sdk/go/pkg/models/openai"
)

const modelName = "text-generator"

// Function to normalize sports commentary using LLaMA
func NormalizeSportsCommentary(rawText string) (string, error) {
    model, err := models.GetModel[openai.ChatModel](modelName)
    if err != nil {
        return "", err
    }

    // Instruction tailored for sports commentary normalization
    instruction := `Normalize the given sports commentary into structured terms.
    Do it for each sentence. Give a normalized sport term for each sentence.
    If phrase have high emphasis then put two exclamation marks to that term like "term!!". 
    If phrase has medium emphasis then put one exclamation mark like "term!". 
    If Phrase has low emphasis then put no exclamation like "term".
    Return the terms as a list in this exact format: [term1, term2 if applicable, term3 if applicable]. 
    Include only normalized terms relevant to the commentary context like just the term and no explanations or anything unnecessary.`

    // Use the raw text as the prompt
    input, err := model.CreateInput(
        openai.NewSystemMessage(instruction),
        openai.NewUserMessage(rawText),
    )
    if err != nil {
        return "", err
    }

    // Optional: Adjust temperature for controlled randomness
    input.Temperature = 0.7

    // Invoke the model
    output, err := model.Invoke(input)
    if err != nil {
        return "", err
    }

    // Trim and return the formatted output
    normalizedText := strings.TrimSpace(output.Choices[0].Message.Content)
    return normalizedText, nil
}
