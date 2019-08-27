package routes

import (
	"github.com/gin-gonic/gin"
	"net/http"
    "github.com/f26401004/ATG-io-platform-backend/models/userModel"
    "os/exec"
    "time"
    "context"
    "bytes"
    "errors"
    "fmt"
    "regexp"
    "io/ioutil"
    "os"
    "strings"
    "strconv"
    "github.com/f26401004/ATG-io-platform-backend/util"
)

func CompileEndpoint (c *gin.Context) {
    // get the username from query
    username := c.Query("username")
    // check if the username has been registered
    _, getUserError := userModel.GetUser(username)
    if (getUserError != nil) {
        c.String(http.StatusBadRequest, getUserError.Error());
        return;
    }
    // compile with the compiler
    _, compilerError := compileGPlusPlus(username)
    if (compilerError != nil) {
        fmt.Println(compilerError)
        c.String(http.StatusInternalServerError, compilerError.Error());
        return;
    }
    // check the third-party package
    _, thirdPackageError := CheckThirdPartyPackage(username)
    if (thirdPackageError != nil) {
        fmt.Println(thirdPackageError)
        c.String(http.StatusInternalServerError, thirdPackageError.Error());
        return;
    }
    // check the third-party package
    _, latencyFormatError := checkLatencyAndFormat(username)
    if (latencyFormatError != nil) {
        fmt.Println(latencyFormatError)
        c.String(http.StatusInternalServerError, latencyFormatError.Error());
        return;
    }
    c.String(http.StatusOK, "Compile result: pass")
    // transfer the code to storage
    transferCode(username)
}

func transferCode(username string) (bool, error) {
    var bucket, projectID string
    bucket = "ATG_io_code_storage"
    projectID = util.MustGetEnv("GOLANG_PROJECT_ID", projectID)
    
    // open the code file
    code, errOpen := os.OpenFile(fmt.Sprintf("./codes/%s.cpp", username), os.O_RDWR|os.O_CREATE, 0755)
    defer code.Close()
    if (errOpen != nil) {
        return false, errOpen
    }
    // store the user code into google cloud storage
    ctx := context.Background()
    _, _, errUpload := util.UploadToStorage(ctx, code, projectID, bucket, username, false)
    if (errUpload != nil) {
        return false, errUpload
    }
    return true, nil
}

func compileGPlusPlus (username string) (bool, error) {
	// set the timeout for safety
	ctx, cancel := context.WithTimeout(context.Background(), 4 * time.Second)
	defer cancel()
  
	// use the buffer to get the output message
	var errorBuffer bytes.Buffer
	var outputBuffer bytes.Buffer
  
    // initialize the command instance
    // here we use C++11 to compile the code.
	argstr := []string{ "-c", fmt.Sprintf("g++ -std=c++11 -o ./bins/%s ./codes/%s.cpp", username, username) }
	cmd := exec.CommandContext(ctx, "/bin/sh", argstr...)
	cmd.Stderr = &errorBuffer
	cmd.Stdout = &outputBuffer
	// run the command
	err := cmd.Run()
	if (err != nil) {
	    return false, err
	}
	// if the output is non-empty, then return the error message to the client
	if (len(outputBuffer.String()) > 0) {
	    return false, errors.New(outputBuffer.String())
	}
    return true, nil
}

func hasElem (slice []string, ele string) (bool) {
    for _, value := range slice {
        if (value == ele) {
        return true
        }
    }
    return false
}

func CheckThirdPartyPackage (username string) (bool, error) {
    // predefine the white list here
    whitelist := []string{"cstring", "cmath", "iostream", "cstdio", "string", "vector", "list", "forward_list", "deque", "array", "map", "set", "unordered_set", "unordered_map"};
    file, err := os.Open(fmt.Sprintf("./codes/%s.cpp", username))
    if (err != nil) {
        return false, err
    }
    defer file.Close()
    
    // read the bytes from the file
    bytes, err := ioutil.ReadAll(file)
    // use regular expression ot find the matched string
    var pattern string = `#include *?<.*>`
    re := regexp.MustCompile(pattern)
    matched := re.FindAll(bytes, -1)
    var check bool = true
    for _, m := range matched {
        rePackageName := regexp.MustCompile(`<.*>`)
        packageName := strings.Replace(strings.Replace(string(rePackageName.Find(m)), "<", "", -1), ">", "", -1)
        // if the length of the package name is zero, then break directly 
        if (len(packageName) == 0) {
            check = false
            break
        }
        // if the whitelist do not include the package name, then break directly
        if (!hasElem(whitelist, packageName)) {
            check = false
            break
        }
    }
	return check, nil
}

func checkLatencyAndFormat(username string) (bool, error) {
    // open the test case file
    testCase, errTestCase := os.Open("./codes/test.txt")
    if (errTestCase != nil) {
        return false, errTestCase
        }
    defer testCase.Close()
    // read the bytes from the test case file
    testCaseBytes, errReadBytes := ioutil.ReadAll(testCase)
    if (errReadBytes != nil) {
        return false, nil
    }

    // set the timeout for safety
    ctx, cancel := context.WithTimeout(context.Background(), 1 * time.Second)
    defer cancel()
    // initialize the command instance
    // here we use C++11 to compile the code.
    argstr := []string{ "-c", fmt.Sprintf("./bins/%s", username) }
    cmd := exec.CommandContext(ctx, "/bin/sh", argstr...)

    // open the process stdout channel
    output, errOutput := cmd.StdoutPipe()
    defer output.Close()
    if (errOutput != nil) {
        return false, errOutput
    }
    // open the process stdin channel
    input, errInput := cmd.StdinPipe()
    if (errInput != nil) {
        return false, errInput
    }
    defer input.Close()

    // run the command with goroutine
    go cmd.Run()
    
    // write the test case to the process
    _, errWrite := input.Write(testCaseBytes)
    if (errWrite != nil) {
        return false, errWrite
    }
    // read the response from the process
    content, _ := ioutil.ReadAll(output)

    var str string = string(content)
    // check if the length of the output message is zero
    if (len(str) == 0) {
        return false, errors.New("Your code is stucked, please check if there is any logic error.")
    }
    newlineSymbol := str[len(str) - 1:len(str)]
    // check the newline symbol
    if (newlineSymbol != "\n") {
        return false, errors.New("The message format wrong, please check if there is any logic error.")
    }
    str = str[0:len(str)-1]
    // check if the number of the action flag is not equal to 6
    sliced := strings.Split(str, " ")
    if (len(sliced) != 6) {
        return false, errors.New("The message format wrong, please check if there is any logic error.")
    }
    // check every action flag format
    for index, value := range sliced {
        transformed, errFloat := strconv.ParseFloat(value, 32)
        if (errFloat != nil) {
            return false, errFloat
        }
        if (index == 0 && !(transformed == 0.0 || transformed == 1.0)) {
            return false, errors.New("The shoot flag must be either one or zero")
        }
        if (index == 1 && (transformed > 1.0 || transformed < 0.0)) {
            return false, errors.New("The shoot angle must be mapped into one to zero.")
        }
        if (index > 1 && !(transformed == 0.0 || transformed == 1.0)) {
            return false, errors.New("The move direction flag must be either one or zero.")
        }
    }
    return true, nil
}