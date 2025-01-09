function Run-File($APIDir, $fileName) {

    $dir = Get-Location

    if($fileName -ne "visualiser")
    {
        #python .\$APIDir"\"$fileName
        $cmd = python .\$APIDir"\"$fileName
        Start-Process powershell $cmd
        Write-Output("opened "+ $APIDir+"\"+$fileName)
    }else{
        $cmd =  "bokeh serve --show"+" "+$dir+"\"+$APIDir+"\"+"$fileName"
    }
}





