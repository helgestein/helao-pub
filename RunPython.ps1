$dir = Get-Location

."$dir\Run-File.ps1"

$list_of_directories = "server"
#, "action", "orchestrators", "visualiser"
$list_server = "fibonacci.py", "fibonacci2.py"
#$list_server = "autolab_server.py", "megsv_server.py", "minipump_server.py", "pump_server.py" , "lang_server.py"
$list_action = "echem.py", "lang_action.py", "minipumping.py", "pumping.py", "sensing_megsv.py"

foreach ($dir in $list_of_directories)
{
  if($dir -eq "server")
  {
    foreach($file in $list_server)
    {
        Run-File $dir $file
    }   
  }

  if($dir -eq "action")
  {
    foreach($file in $list_action)
    {
        Run-File($dir, $file)
    }   
  }

  if($dir -eq "orchestrators")
  {
    Run-File($dir, "mischbares.py") 
  }

  if($dir -eq "visualiser")
  {
    Run-File($dir, "autolab_visualizer.py") 
  }


}

Start-Process powershell "python process.py"
Write-Output("Started python process")