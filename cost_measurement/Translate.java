import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;

public class Translate
{
  private static Process procReplay;
  
  public static void main(String[] args)
  {
    String line = "";
    String inputDeviceType = "";
    long type = 0L;
    long code = 0L;
    long value = 0L;
    double prevTimestamp = 0.0D;
    int sameCounter = 0;
    boolean allEventsValid = false;
    
    File wd = new File("/bin");
    try
    {
      procReplay = Runtime.getRuntime().exec("/bin/bash", null, wd);
    }
    catch (IOException e)
    {
      e.printStackTrace();
    }
    if (procReplay != null)
    {
      String eventsFilePath = args[0];
      String splitEventOn = ",";
      String[] validEventNumbers = null;
      if (args.length >= 3)
      {
        int parameterIndexE = parameterCheck(args, "-e");
        if (parameterIndexE > 0) {
          validEventNumbers = args[parameterIndexE].split(splitEventOn);
        } else {
          allEventsValid = true;
        }
      }
      else
      {
        allEventsValid = true;
      }
      int numberOfLines = 0;
      try
      {
        BufferedReader reader = new BufferedReader(new FileReader(eventsFilePath));
        
        String temp = "";
        while ((temp = reader.readLine()) != null) {
          if ((temp.lastIndexOf("event") != -1) && (temp.lastIndexOf("device") == -1) && (temp.lastIndexOf("name") == -1))
          {
            String[] tokens = null;
            String splitOn = " ";
            
            tokens = temp.split(splitOn);
            
            inputDeviceType = tokens[1];
            inputDeviceType = removeColon(inputDeviceType);
            String eventNumber = getInputDevice(inputDeviceType);
            int currentEventIsValid = 0;
            if (!allEventsValid)
            {
              for (int x = 0; x < validEventNumbers.length; x++) {
                if (eventNumber.equals(validEventNumbers[x])) {
                  currentEventIsValid = 1;
                }
              }
              if (currentEventIsValid == 1) {
                numberOfLines++;
              }
            }
            else
            {
              numberOfLines++;
            }
          }
        }
        reader.close();
      }
      catch (Exception e)
      {
        e.printStackTrace();
      }
      File eventsFile = new File(eventsFilePath);
      InputStream inStream = null;
      try
      {
        inStream = new FileInputStream(eventsFile);
      }
      catch (FileNotFoundException e2)
      {
        e2.printStackTrace();
      }
      DataInputStream inDataStream = new DataInputStream(inStream);
      BufferedReader fileReader = new BufferedReader(new InputStreamReader(inDataStream));
      
      PrintStream output = null;
      try
      {
        FileOutputStream outputStream = new FileOutputStream(args[1]);
        output = new PrintStream(outputStream);
      }
      catch (IOException e3)
      {
        e3.printStackTrace();
      }
      boolean isFirstEvent = true;
      output.println(numberOfLines);
      int written = 0;
      try
      {
        while ((line = fileReader.readLine()) != null)
        {
          String[] tokens = null;
          String timestampString = "";
          String timestampLine = "";
          double timestamp = 0.0D;
          long interval = 0L;
          String splitOn = " ";
          int seconds = 0;
          int microseconds = 0;
          int idx = -1;
          
          // line = line.substring(1:);
          // line = line.strip();
          tokens = line.split(splitOn);
          timestampString = tokens[0];
          if ((!timestampString.equals("add")) && (timestampString.length() != 0) && (!timestampString.equals("could")))
          { 
            for (int i=1; i<tokens.length; i++)
            {
              String token = tokens[i];
              if (!token.equals(""))
               {
                idx = i;
                break;
               }
            }
            timestampLine = tokens[idx].replace("]", "");
      
            String[] times = null;
            timestampLine = timestampLine.replace(".", " ");
            
            times = timestampLine.split(" ");

            seconds = stringToInt(times[0]);
            microseconds = stringToInt(times[1]);
            timestamp = seconds + microseconds / 1000000.0D;
            
            inputDeviceType = tokens[idx+1];
            inputDeviceType = removeColon(inputDeviceType);
            String eventNumber = getInputDevice(inputDeviceType);
            
            boolean currentEventIsValid = false;
            if (!allEventsValid) {
              for (int x = 0; x < validEventNumbers.length; x++) {
                if (eventNumber.equals(validEventNumbers[x])) {
                  currentEventIsValid = true;
                }
              }
            }
            if (((currentEventIsValid) && (!eventNumber.equals("*"))) || ((allEventsValid) && (!eventNumber.equals("*"))))
            {
              type = hexToLong(tokens[idx+2]);
              code = hexToLong(tokens[idx+3]);
              value = hexToLong(tokens[idx+4]);
              if (isFirstEvent) {
                prevTimestamp = timestamp;
              }
              long longTimestamp = (long)(timestamp * 1.0E9D);
              long longPrevTimestamp = (long)(prevTimestamp * 1.0E9D);
              interval = longTimestamp - longPrevTimestamp;
              if (interval >= 0L)
              {
                long intervalNano = interval;
                if (args.length >= 3)
                {
                  int parameterIndexT = parameterCheck(args, "-t");
                  if (parameterIndexT > 0)
                  {
                    String[] timeWarpingValues = null;
                    timeWarpingValues = args[parameterIndexT].split(",");
                    long min = (long)(1.0E9F * Float.parseFloat(timeWarpingValues[0]));
                    long low = (long)(1.0E9F * Float.parseFloat(timeWarpingValues[1]));
                    long newValue = (long)(1.0E9F * Float.parseFloat(timeWarpingValues[2]));
                    long max = (long)(1.0E9F * Float.parseFloat(timeWarpingValues[3]));
                    if ((min >= low) || (min >= max) || (low >= max)) {
                      throw new IOException("ERROR: Bad range of time-warp values, check documentation.");
                    }
                    if ((intervalNano > min) && 
                      (intervalNano < low)) {
                      intervalNano = newValue;
                    } else if (intervalNano > max) {
                      intervalNano = max;
                    }
                  }
                }
                try
                {
                  if (intervalNano == 0L) {
                    sameCounter++;
                  }
                  output.println(intervalNano);
                }
                catch (Exception e)
                {
                  e.printStackTrace();
                }
              }
              else
              {
                System.out.println("ERROR, time interval between events should not be negative! Please check getevent log for event types that can be ignored.");
                break;
              }
              output.println(eventNumber + "," + type + "," + code + "," + value);
              
              written++;
              prevTimestamp = timestamp;
              if (isFirstEvent) {
                isFirstEvent = false;
              }
            }
          }
        }
      }
      catch (IOException e1)
      {
        e1.printStackTrace();
      }
      System.out.println("Total number of events written is " + written);
      try
      {
        inStream.close();
        inDataStream.close();
        fileReader.close();
      }
      catch (Exception e)
      {
        e.printStackTrace();System.out.println("Error!");
      }
    }
  }
  
  static long hexToLong(String hex)
  {
    return Long.parseLong(hex, 16);
  }
  
  static String getInputDevice(String path)
  {
    return path.replaceAll("/dev/input/event", "");
  }
  
  static String removeColon(String original)
  {
    return original.replaceAll(":", "");
  }
  
  static int stringToInt(String s)
  {
    return Integer.parseInt(s);
  }
  
  static long stringToLong(String s)
  {
    return Long.parseLong(s);
  }
  
  static double timestampToSeconds(String timestamp)
  {
    timestamp = timestamp.replaceAll("-", ".");
    return Double.parseDouble(timestamp);
  }
  
  static int parameterCheck(String[] args, String flag)
  {
    boolean found = false;
    int i;
    for (i = 0; i < args.length; i++) {
      if (args[i].equals(flag))
      {
        found = true;
        break;
      }
    }
    if (!found) {
      i = -2;
    }
    return i + 1;
  }
}
