// SPDX-License-Identifier: MIT
pragma solidity ^0.7.4;

contract GameOfLife {
    int16 constant rows = 32;
    int16 constant cols = 32;
    uint256[] public cells;
    uint256[] newcells;
    int public iterations;
    uint public myblock;
    
    event log(string text);
    event Cells(uint256[] cells);

    constructor ()  {
        // a bit for each cell - stored in an array of 256 bit numbers
        // for default of  32 x 32 this is 4 x 256 bit numbers
        cells = new uint256[](uint16(rows * cols) / 256);

        newcells = cells;

        // set up a few 'sliders'
        for (int16 i=0; i<20; i +=6) {
            int16 pos;
            pos = ((i+1) + (i+1)*cols) ;
            set(pos,1);
            pos = ((i+2) + (i+2)*cols) ;
            set(pos,1);
            pos = ((i+3) + (i+2)*cols) ;
            set(pos,1);
            pos = ((i+1) + (i+3)*cols) ;
            set(pos,1);
            pos = ((i+2) + (i+3)*cols) ;
            set(pos,1);
        }
        
        cells = newcells;
    }
    
   
    // get for a particular row/col return the cell state (1 alive, 0 dead)
    function get(int32 pos) view internal returns (int) {

        if (pos<0) {
            pos += rows*cols;
        } 
        if (pos >= rows*cols) {
            pos -= rows*cols;
        }
        // make sure pos always is a valid value
        pos = pos % int32(rows*cols);
        // the linear array is held in 4 x 256 unsigned integers
        uint32 i = uint32(pos) / 256;
        uint32 j = uint32(pos) % 256;
        // if the j-th bit set?
        if ((cells[i] >> j) & 0x01 == 1 ) {
            return 1;
        } else {
            return 0;
        }
    }
    function set(int16 pos, int8 value) internal {
        // the linear array is held in 4 x 256 unsigned integers 
        uint32 i = uint32(pos) / 256;
        uint32 j = uint32(pos) % 256;
        // if value is 1 then set the j-th bit
        if (value>0){
            newcells[i] |= (1 << j);  // set this bit
        } else {
            newcells[i] &= ~(1 << j);  // turn off this bit
        }
        
    }

// Overpopulation: if a living cell is surrounded by more than three living cells, it dies.
// Stasis: if a living cell is surrounded by two or three living cells, it survives.
// Underpopulation: if a living cell is surrounded by fewer than two living cells, it dies.
// Reproduction: if a dead cell is surrounded by exactly three cells, it becomes a live cell.
   
    // step - perform a single step of the Conway's game of life
    function step() public {
        
        newcells = new uint256[](cells.length);
        // skip the edge row/col to avoid checking for out of bounds
        // skip some more to reduce the amount of gas needed.
        for (int16 row=4; row<rows-4; row++) {
            for (int16 col=4; col<cols-4; col++) {
                
                int16 pos = (col + row*cols);
                int count = 0;

                // count_neighbours - count the number of cells that are direct neighbours   
                count += get(pos - cols - 1);  //(row-1,col-1); 
                count += get(pos - cols);      //(row-1,col  );
                count += get(pos - cols + 1);  //row-1,col+1);
                
                count += get(pos - 1); //(row,col-1);
                count += get(pos + 1); //(row,col+1);
                
                count += get(pos + cols -1); //(row+1,col-1);
                count += get(pos + cols); //(row+1,col  );
                count += get(pos + cols + 1); //(row+1,col+1);
                        
                // if current cell is alive
                if (get(pos) == 1) {
                    if (count > 3) {
                        set(pos,0);
                    } else if (count == 2 || count == 3) {
                        set(pos,1);
                    } else if (count < 2) {
                        set(pos,0);
                    }
                } else { // dead cell
                    if (count == 3) {
                        set(pos,1);
                    }
                }
            }
            
        }
        cells = newcells;

        myblock = block.number;
        //emit Cells(cells);
    }
    
    function getCells() public view returns (uint256[] memory) {
        return cells;
    }

    function getMyBlock() public view returns (uint256) {
        return myblock;
    }
    
    function setCells(uint256 c0, uint256 c1, uint256 c2, uint256 c3) public {
        cells[0] = c0;
        cells[1] = c1;
        cells[2] = c2;
        cells[3] = c3;

        myblock = block.number;
    }   
}