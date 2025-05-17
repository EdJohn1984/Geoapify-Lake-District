import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function GET() {
  try {
    const pythonScript = path.join(process.cwd(), 'hiking_planner/src/brecon_planner.py');
    console.log('Executing Python script:', pythonScript);
    
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python3', [pythonScript], {
        env: {
          ...process.env,
          PYTHONPATH: process.cwd()
        }
      });
      
      let output = '';
      let error = '';
      
      pythonProcess.stdout.on('data', (data: Buffer) => {
        const chunk = data.toString();
        console.log('Python stdout:', chunk);
        output += chunk;
      });
      
      pythonProcess.stderr.on('data', (data: Buffer) => {
        const chunk = data.toString();
        console.error('Python stderr:', chunk);
        error += chunk;
      });
      
      pythonProcess.on('close', (code: number) => {
        console.log('Python process exited with code:', code);
        console.log('Final output:', output);
        console.log('Final error:', error);
        
        if (code !== 0) {
          reject(NextResponse.json({ 
            error: 'Failed to generate itinerary',
            details: error,
            exitCode: code
          }, { status: 500 }));
        } else {
          try {
            if (!output.trim()) {
              throw new Error('No output received from Python script');
            }
            // Parse the JSON output from Python
            const result = JSON.parse(output);
            resolve(NextResponse.json(result));
          } catch (parseError) {
            console.error('JSON parse error:', parseError);
            reject(NextResponse.json({ 
              error: 'Invalid response from itinerary generator',
              details: output,
              parseError: parseError instanceof Error ? parseError.message : 'Unknown parse error'
            }, { status: 500 }));
          }
        }
      });
    });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to generate itinerary',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
} 