import * as muiColors from '@mui/material/colors';

export const moneyColors = {
    light: {
        income: muiColors.green[500],
        expense: muiColors.red[500],
    },
    dark: {
        income: muiColors.green[300],
        expense: muiColors.red[300],
    },
};

export const monthColors = {
    light: [
        muiColors.red[100],
        muiColors.pink[100],
        muiColors.purple[100],
        muiColors.yellow[100],
        muiColors.orange[100],
        muiColors.blue[100],
        muiColors.lightBlue[100],
        muiColors.cyan[100],
        muiColors.teal[100],
        muiColors.green[100],
        muiColors.lightGreen[100],
        muiColors.lime[100],
        muiColors.blueGrey[100],
        // second shade
        muiColors.red[300],
        muiColors.pink[300],
        muiColors.purple[300],
        muiColors.yellow[300],
        muiColors.orange[300],
        muiColors.blue[300],
        muiColors.lightBlue[300],
        muiColors.cyan[300],
        muiColors.teal[300],
        muiColors.green[300],
        muiColors.lightGreen[300],
        muiColors.lime[300],
        muiColors.blueGrey[300],
    ],
    dark: [
        muiColors.red[900],
        muiColors.pink[900],
        muiColors.purple[900],
        muiColors.yellow[900],
        muiColors.orange[900],
        muiColors.blue[900],
        muiColors.lightBlue[900],
        muiColors.cyan[900],
        muiColors.teal[900],
        muiColors.green[900],
        muiColors.lightGreen[900],
        muiColors.lime[900],
        muiColors.blueGrey[900],
        // second shade
        muiColors.red[700],
        muiColors.pink[700],
        muiColors.purple[700],
        muiColors.yellow[700],
        muiColors.orange[700],
        muiColors.blue[700],
        muiColors.lightBlue[700],
        muiColors.cyan[700],
        muiColors.teal[700],
        muiColors.green[700],
        muiColors.lightGreen[700],
        muiColors.lime[700],
        muiColors.blueGrey[700],
    ],
};

// Taken from https://github.com/eriese/bin-pack-with-constraints
export class GrowingPacker {
    maxWidth: number;
    maxHeight: number;
    strictMax: boolean;
    ensureSquare: boolean;
    root: any;

    constructor(maxWidth = Infinity, maxHeight = Infinity, strictMax = false) {
        this.maxWidth = maxWidth
        this.maxHeight = maxHeight
        this.strictMax = strictMax
        this.ensureSquare = maxWidth === Infinity && maxHeight === Infinity
    }

    fit(blocks) {
		var len = blocks.length
		if (len === 0) { return }

		var n, node, block, fit;
		var width  = this.strictMax && (this.maxWidth < Infinity) ? this.maxWidth : blocks[0].width;
		var height  = this.strictMax && (this.maxHeight < Infinity) ? this.maxHeight : blocks[0].height;
		this.root = { x: 0, y: 0, width, height };
		for (n = 0; n < len ; n++) {
			block = blocks[n];
			if (node = this.findNode(this.root, block.width, block.height)) {
				fit = this.splitNode(node, block.width, block.height);
				block.x = fit.x;
				block.y = fit.y;
			}
			else {
				fit = this.growNode(block.width, block.height);
				block.x = fit.x;
				block.y = fit.y;
			}
		}
	}

	findNode(root, width, height) {
		if (root.used)
			return this.findNode(root.right, width, height) || this.findNode(root.down, width, height);
		else if (width <= root.width && height <= root.height)
			return root;
		else
			return null;
	}

	splitNode(node, width, height) {
		node.used = true;
		const downY = node.y + height
		node.down  = {
			x: node.x,
			y: downY,
			width: node.width,
			height: Math.min(node.height - height, this.maxHeight - downY)
		};

		const rightX = node.x + width
		node.right = {
			x: rightX,
			y: node.y,
			width: Math.min(node.width - width, this.maxWidth - rightX),
			height: height
		};
		return node;
	}

	growNode(width, height) {
		var canGrowDown  = width  <= this.root.width;
		var canGrowRight = height <= this.root.height;

		const proposedNewWidth = this.root.width + width
		var shouldGrowRight = canGrowRight && (this.ensureSquare ? this.root.height : this.maxWidth) >= proposedNewWidth; // attempt to keep square-ish by growing right when height is much greater than width
		const proposedNewHeight = this.root.height + height
		var shouldGrowDown  = canGrowDown  && (this.ensureSquare ? this.root.width : this.maxHeight) >= proposedNewHeight; // attempt to keep square-ish by growing down  when width  is much greater than height

		if (shouldGrowRight)
			return this.growRight(width, height);
		else if (shouldGrowDown)
			return this.growDown(width, height);
		else if (canGrowRight)
			return this.growRight(width, height);
		else if (canGrowDown)
			return this.growDown(width, height);
		else
			return null; // need to ensure sensible root starting size to avoid this happening
	}

	growRight(width, height) {
		this.root = {
			used: true,
			x: 0,
			y: 0,
			width: this.root.width + width,
			height: this.root.height,
			down: this.root,
			right: { x: this.root.width, y: 0, width: width, height: this.root.height }
		};
		var node;
		if (node = this.findNode(this.root, width, height))
			return this.splitNode(node, width, height);
		else
			return null;
	}

	growDown(width, height) {
		this.root = {
			used: true,
			x: 0,
			y: 0,
			width: this.root.width,
			height: this.root.height + height,
			down:  { x: 0, y: this.root.height, width: this.root.width, height: height },
			right: this.root
		};
		var node;
		if (node = this.findNode(this.root, width, height))
			return this.splitNode(node, width, height);
		else
			return null;
	}
}
