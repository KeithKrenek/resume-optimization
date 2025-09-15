// app.js - Resume Optimizer Application
const express = require('express');
const multer = require('multer');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const { OpenAI } = require('openai');
const pdfParse = require('pdf-parse');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || 'http://localhost:3000',
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// File upload configuration
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'text/plain',
      'text/markdown',
      'application/json',
      'application/pdf'
    ];
    
    const allowedExtensions = ['.txt', '.md', '.json', '.pdf'];
    const fileExtension = path.extname(file.originalname).toLowerCase();
    
    if (allowedTypes.includes(file.mimetype) || allowedExtensions.includes(fileExtension)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only TXT, Markdown, JSON, and PDF files are allowed.'), false);
    }
  }
});

// Assistant ID - should be configured in environment
const ASSISTANT_ID = process.env.OPENAI_ASSISTANT_ID;

// Middleware to validate environment variables
const validateEnvironment = (req, res, next) => {
  if (!process.env.OPENAI_API_KEY) {
    return res.status(500).json({ 
      error: 'Server configuration error: OpenAI API key not configured' 
    });
  }
  
  if (!ASSISTANT_ID) {
    return res.status(500).json({ 
      error: 'Server configuration error: OpenAI Assistant ID not configured' 
    });
  }
  
  next();
};

// Utility function to parse uploaded files
async function parseResumeFile(file) {
  try {
    const buffer = file.buffer;
    const extension = path.extname(file.originalname).toLowerCase();
    
    switch (extension) {
      case '.txt':
      case '.md':
        return buffer.toString('utf-8');
      
      case '.json':
        try {
          return JSON.stringify(JSON.parse(buffer.toString('utf-8')), null, 2);
        } catch (e) {
          throw new Error('Invalid JSON format in uploaded file');
        }
      
      case '.pdf':
        try {
          const pdfData = await pdfParse(buffer);
          return pdfData.text;
        } catch (e) {
          throw new Error('Unable to extract text from PDF file');
        }
      
      default:
        throw new Error('Unsupported file format');
    }
  } catch (error) {
    throw new Error(`File parsing error: ${error.message}`);
  }
}

// Utility function to create and manage OpenAI thread
async function createThreadAndRun(jobDescription, companyURL, resumeContent) {
  try {
    // Create a thread
    const thread = await openai.beta.threads.create();
    
    // Create the message with all the required information
    const message = await openai.beta.threads.messages.create(thread.id, {
      role: "user",
      content: `
Please analyze the following information and create an optimized resume:

JOB DESCRIPTION:
${jobDescription}

COMPANY URL: ${companyURL}

CURRENT RESUME:
${resumeContent}

Please research the company and role requirements, then optimize the resume to better match the job description. Return the result as a properly formatted JSON object with the following structure:
{
  "personalInfo": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "website": ""
  },
  "summary": "",
  "experience": [
    {
      "title": "",
      "company": "",
      "location": "",
      "startDate": "",
      "endDate": "",
      "description": [""]
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "location": "",
      "graduationDate": ""
    }
  ],
  "skills": {
    "technical": [""],
    "soft": [""]
  },
  "projects": [
    {
      "name": "",
      "description": "",
      "technologies": [""],
      "url": ""
    }
  ],
  "certifications": [
    {
      "name": "",
      "issuer": "",
      "date": "",
      "url": ""
    }
  ]
}

Focus on:
1. Tailoring the summary to match the job requirements
2. Highlighting relevant experience and achievements
3. Optimizing keywords for ATS systems
4. Ensuring the resume is compelling and professional
`
    });

    // Run the assistant
    const run = await openai.beta.threads.runs.create(thread.id, {
      assistant_id: ASSISTANT_ID,
      instructions: "You are a professional resume optimization expert. Research the provided company and job description thoroughly, then create an optimized resume that maximizes the candidate's chances of getting the position. Always return valid JSON format."
    });

    return { threadId: thread.id, runId: run.id };
  } catch (error) {
    throw new Error(`OpenAI API error: ${error.message}`);
  }
}

// Utility function to wait for run completion and get result
async function waitForRunCompletion(threadId, runId, maxAttempts = 30) {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const run = await openai.beta.threads.runs.retrieve(threadId, runId);
      
      if (run.status === 'completed') {
        // Get the messages from the thread
        const messages = await openai.beta.threads.messages.list(threadId);
        const assistantMessage = messages.data.find(msg => msg.role === 'assistant');
        
        if (assistantMessage && assistantMessage.content[0]?.text?.value) {
          return assistantMessage.content[0].text.value;
        } else {
          throw new Error('No response content found from assistant');
        }
      } else if (run.status === 'failed') {
        throw new Error(`Assistant run failed: ${run.last_error?.message || 'Unknown error'}`);
      } else if (run.status === 'cancelled') {
        throw new Error('Assistant run was cancelled');
      } else if (run.status === 'expired') {
        throw new Error('Assistant run expired');
      }
      
      // Wait 2 seconds before checking again
      await new Promise(resolve => setTimeout(resolve, 2000));
      attempts++;
    } catch (error) {
      if (error.message.includes('Assistant run failed') || 
          error.message.includes('cancelled') || 
          error.message.includes('expired')) {
        throw error;
      }
      // For other errors, continue trying
      attempts++;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  throw new Error('Timeout waiting for assistant response');
}

// Utility function to extract JSON from response
function extractJSON(responseText) {
  try {
    // First try to parse directly
    return JSON.parse(responseText);
  } catch (e) {
    // Try to find JSON within the response
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      try {
        return JSON.parse(jsonMatch[0]);
      } catch (e2) {
        throw new Error('Unable to parse JSON from assistant response');
      }
    } else {
      throw new Error('No JSON found in assistant response');
    }
  }
}

// Serve static files (for the frontend)
app.use(express.static('public'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Main resume optimization endpoint
app.post('/optimize-resume', validateEnvironment, upload.single('resume'), async (req, res) => {
  try {
    // Validate required fields
    const { jobDescription, companyURL } = req.body;
    
    if (!jobDescription || jobDescription.trim().length === 0) {
      return res.status(400).json({ 
        error: 'Job description is required and cannot be empty' 
      });
    }
    
    if (!companyURL || companyURL.trim().length === 0) {
      return res.status(400).json({ 
        error: 'Company URL is required and cannot be empty' 
      });
    }
    
    if (!req.file) {
      return res.status(400).json({ 
        error: 'Resume file is required' 
      });
    }

    // Parse the uploaded resume file
    let resumeContent;
    try {
      resumeContent = await parseResumeFile(req.file);
    } catch (error) {
      return res.status(400).json({ 
        error: error.message 
      });
    }

    // Create thread and run with OpenAI Assistant
    const { threadId, runId } = await createThreadAndRun(
      jobDescription.trim(),
      companyURL.trim(),
      resumeContent
    );

    // Wait for completion and get result
    const assistantResponse = await waitForRunCompletion(threadId, runId);
    
    // Extract and validate JSON
    const optimizedResumeJSON = extractJSON(assistantResponse);
    
    // Return the optimized resume
    res.json({
      success: true,
      optimizedResume: optimizedResumeJSON,
      metadata: {
        originalFileName: req.file.originalname,
        processedAt: new Date().toISOString(),
        threadId: threadId
      }
    });

  } catch (error) {
    console.error('Resume optimization error:', error);
    
    // Return appropriate error response
    if (error.message.includes('OpenAI API error')) {
      res.status(502).json({ 
        error: 'External service error. Please try again later.',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    } else if (error.message.includes('Timeout')) {
      res.status(504).json({ 
        error: 'Request timeout. The resume optimization is taking longer than expected. Please try again.' 
      });
    } else {
      res.status(500).json({ 
        error: 'Internal server error. Please try again later.',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'File too large. Maximum size is 10MB.' });
    }
    return res.status(400).json({ error: 'File upload error: ' + error.message });
  }
  
  console.error('Unhandled error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Resume Optimizer server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  
  // Validate environment on startup
  if (!process.env.OPENAI_API_KEY) {
    console.warn('⚠️  WARNING: OPENAI_API_KEY environment variable not set');
  }
  if (!ASSISTANT_ID) {
    console.warn('⚠️  WARNING: OPENAI_ASSISTANT_ID environment variable not set');
  }
});

module.exports = app;