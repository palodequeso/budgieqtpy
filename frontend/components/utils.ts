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
        '#8B1515',  // Red - darker than 900
        '#6B0A3C',  // Pink - darker than 900
        '#380F6B',  // Purple - darker than 900
        '#9D6A0A',  // Yellow/Gold - much darker for contrast
        '#B84000',  // Orange - darker than 900
        '#0A3677',  // Blue - darker than 900
        '#014477',  // Light Blue - darker than 900
        '#004D50',  // Cyan - darker than 900
        '#003D32',  // Teal - darker than 900
        '#154718',  // Green - darker than 900
        '#285216',  // Light Green - darker than 900
        '#665E12',  // Lime/Olive - darker than 900
        '#1C262B',  // Blue Grey - darker than 900
        // second shade (900 shades for variety)
        '#B71C1C',  // Red 900
        '#880E4F',  // Pink 900
        '#4A148C',  // Purple 900
        '#C67D0D',  // Yellow/Gold - darker custom shade
        '#E65100',  // Orange 900
        '#0D47A1',  // Blue 900
        '#01579B',  // Light Blue 900
        '#006064',  // Cyan 900
        '#004D40',  // Teal 900
        '#1B5E20',  // Green 900
        '#33691E',  // Light Green 900
        '#827717',  // Lime 900
        '#263238',  // Blue Grey 900
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
