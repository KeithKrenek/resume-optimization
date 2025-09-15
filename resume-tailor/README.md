# Resume Optimizer

Production-ready Node.js app that optimizes resumes using OpenAI Assistants API.

## Quick Start

1. **Setup Environment**
   ```bash
   npm install
   cp .env.example .env
   ```

2. **Configure OpenAI**
   - Get API key from [OpenAI Platform](https://platform.openai.com)
   - Create an Assistant in [OpenAI Playground](https://platform.openai.com/playground)
   - Add credentials to `.env`:
     ```
     OPENAI_API_KEY=your_key_here
     OPENAI_ASSISTANT_ID=asst_your_id_here
     ```

3. **Run Application**
   ```bash
   npm start          # Production
   npm run dev        # Development with auto-reload
   ```

4. **Access Interface**
   - Open http://localhost:3000
   - Upload resume file (PDF, TXT, MD, JSON)
   - Paste job description and company URL
   - Click "Optimize Resume"

## API Endpoint

**POST** `/optimize-resume`

**Form Data:**
- `jobDescription` (text) - Target job description
- `companyURL` (text) - Company website URL  
- `resume` (file) - Resume file (PDF/TXT/MD/JSON, max 10MB)

**Response:**
```json
{
  "success": true,
  "optimizedResume": { /* JSON resume object */ },
  "metadata": { /* processing info */ }
}
```

## Assistant Configuration

Configure your OpenAI Assistant with:

**Instructions:**
```
You are a professional resume optimization expert. Research the provided company and job description thoroughly, then create an optimized resume that maximizes the candidate's chances of getting the position. Always return valid JSON format with the specified structure.
```

**Tools:** Enable File Search and Web Browsing for company research.

## Production Deployment

1. **Environment Variables**
   ```bash
   NODE_ENV=production
   PORT=3000
   OPENAI_API_KEY=your_key
   OPENAI_ASSISTANT_ID=your_assistant_id
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

2. **Security Features**
   - Rate limiting (100 requests/15min per IP)
   - File upload validation
   - CORS protection
   - Security headers (Helmet)
   - Input sanitization

3. **Docker Deployment**
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   EXPOSE 3000
   CMD ["npm", "start"]
   ```

## File Support

- **PDF** - Text extraction via pdf-parse
- **TXT/MD** - Direct text processing
- **JSON** - Resume data structures

## Error Handling

- File validation and parsing errors
- OpenAI API failures with retry logic
- Request timeouts (60s default)
- Rate limiting protection

## Migration Note

⚠️ OpenAI plans to deprecate Assistants API in H1 2026. Consider migrating to the new Responses API when feature parity is achieved.