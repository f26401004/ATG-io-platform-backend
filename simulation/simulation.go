package simulation


import (
    "github.com/gorilla/websocket" 
    // "github.com/f26401004/ATG-io-platform-backend/models/rankModel"
    "time"
    "fmt"
    "os/exec"
    "context"
    "github.com/go-redis/redis"
    "strconv"
)

type Simulation struct {
    Username string
    Status int
    Socket *websocket.Conn
}

var simulationQueue chan Simulation
var resultQueue chan bool

func InitSimulationEnvironment() {
    // initialize simulation and result queue, and the maximum number is 100 at once
    simulationQueue = make(chan Simulation, 100)
    resultQueue = make(chan bool, 100)

    // start 30 goroutine to handle the simulation
    for i := 0; i < 100; i++ {
        go simulationWorker(i)
    }
}

func StartSimulation(username string, socket *websocket.Conn) {
    var info Simulation
    info.Username = username
    info.Status = 0
    info.Socket = socket

    // send the data with channel
    simulationQueue <- info
}


func simulationWorker(id int) {
    for simulation := range simulationQueue {
        fmt.Println("worker", id, "started simulation", simulation.Username)
        // set the timeout to 65 second for safety
        ctx, cancel := context.WithTimeout(context.Background(), 70 * time.Second)
        defer cancel()

        // initialize the command instance
        argstr := []string{ "-c", fmt.Sprintf("python3 ./simulation/sandboxSimulation.py %s %d ", simulation.Username, id) }
        cmd := exec.CommandContext(ctx, "/bin/sh", argstr...)

        // run the command with goroutine
        go cmd.Run()
        // run the receiver with goroutine
        go func (simualtion *Simulation) {
            _, _, errRead := simulation.Socket.ReadMessage()
            // if the closed error exist
            if (errRead != nil) {
                // stop all simualtion process
                simulation.Status = -1
            }
        }(&simulation)
        
        // use redis to implement pubsub
        redisClient := redis.NewClient(&redis.Options{
            Addr: "127.0.0.1:6379",
        })
        defer redisClient.Close()
        idString := strconv.Itoa(id)
        pubsub := redisClient.Subscribe("worker" + idString + "simulation")
        defer pubsub.Close()
        for {
            if (simulation.Status == -1) {
                cancel()
                break
            }
            msg, errReceive := pubsub.ReceiveMessage()
            if (errReceive != nil) {
                simulation.Status = -1
                break
            }
            simulation.Socket.WriteMessage(websocket.TextMessage, []byte(msg.Payload))
        }
        if (simulation.Status == -1) {
            fmt.Println("worker", id, "interrupted simulation", simulation.Username)
        } else {
            fmt.Println("worker", id, "finished simulation", simulation.Username)
        }
        
        // resultQueue <- result
    }
}