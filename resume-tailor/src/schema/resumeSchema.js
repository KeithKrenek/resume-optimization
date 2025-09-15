// src/schema/resumeSchema.js
// JSON Schema for the optimized resume (aligned with Structured Outputs).
// Includes placeholders (e.g., "<add metric>") when the source lacks specifics.
export const resumeSchema = {
  name: "OptimizedResume",
  schema: {
    type: "object",
    additionalProperties: false,
    required: ["version", "target_role", "company", "summary", "skills", "experience"],
    properties: {
      version: { type: "string", const: "1.0" },
      target_role: { type: "string", minLength: 2 },
      company: { type: "string", minLength: 2 },
      tailoring_notes: {
        type: "array",
        items: { type: "string", minLength: 2 }
      },
      summary: { type: "string", minLength: 10 },
      skills: {
        type: "object",
        additionalProperties: false,
        required: ["core", "nice_to_have"],
        properties: {
          core: { type: "array", items: { type: "string" } },
          nice_to_have: { type: "array", items: { type: "string" } }
        }
      },
      experience: {
        type: "array",
        minItems: 1,
        items: {
          type: "object",
          additionalProperties: false,
          required: ["title", "company", "highlights"],
          properties: {
            title: { type: "string" },
            company: { type: "string" },
            location: { type: "string" },
            start_date: { type: "string" },
            end_date: { type: "string" },
            highlights: {
              type: "array",
              minItems: 3,
              items: { type: "string" }
            }
          }
        }
      },
      projects: {
        type: "array",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["name", "highlights"],
          properties: {
            name: { type: "string" },
            link: { type: "string" },
            highlights: { type: "array", items: { type: "string" } }
          }
        }
      },
      education: {
        type: "array",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["institution", "credential"],
          properties: {
            institution: { type: "string" },
            credential: { type: "string" },
            year: { type: "string" }
          }
        }
      },
      certifications: { type: "array", items: { type: "string" } },
      publications: { type: "array", items: { type: "string" } },
      extras: { type: "array", items: { type: "string" } }
    }
  },
  strict: true
};
